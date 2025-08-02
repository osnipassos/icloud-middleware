import requests
import os
import re
from requests.auth import HTTPBasicAuth

ICLOUD_USER = os.environ.get("APPLE_ID")
ICLOUD_PASS = os.environ.get("APPLE_APP_PASSWORD")

HEADERS = {
    "Depth": "1",
    "Content-Type": "application/xml; charset=utf-8",
}

def get_contacts_raw():
    url_base = "https://contacts.icloud.com"
    principal_url = f"{url_base}/.well-known/carddav"

    try:
        r = requests.request("PROPFIND", principal_url, headers=HEADERS, auth=HTTPBasicAuth(ICLOUD_USER, ICLOUD_PASS))
        if r.status_code != 207:
            return {"erro": f"Erro no PROPFIND", "status": r.status_code, "body": r.text}

        hrefs = re.findall(r"<href>(.*?)</href>", r.text)
        addressbook_url = next((h for h in hrefs if "/carddavhome/" in h or "/addressbooks/" in h), None)
        if not addressbook_url:
            return {"erro": "Não encontrou a URL do addressbook", "respostas": hrefs}

        report_body = """<?xml version="1.0" encoding="UTF-8" ?>
<C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
  <D:prop>
    <D:getetag/>
    <C:address-data/>
  </D:prop>
</C:addressbook-query>"""

        full_url = url_base + addressbook_url
        r = requests.request("REPORT", full_url, data=report_body, headers=HEADERS, auth=HTTPBasicAuth(ICLOUD_USER, ICLOUD_PASS))
        if r.status_code != 207:
            return {"erro": "Erro no REPORT", "status": r.status_code, "body": r.text}

        return {"vcard": r.text}
    except Exception as e:
        return {"erro": f"Exceção inesperada: {e}"}


def parse_vcards(vcards_raw: str):
    contatos = []
    vcard_blocks = re.findall(r"BEGIN:VCARD.*?END:VCARD", vcards_raw, re.DOTALL)

    for vcard in vcard_blocks:
        contato = {
            "nome": None,
            "nome_completo": None,
            "apelido": None,
            "email": [],
            "telefone": [],
            "empresa": None,
            "cargo": None,
            "endereco": [],
            "aniversario": None,
            "notas": None,
            "linkedin": None,
            "outras_redes": {},
            "websites": [],
            "tags": [],
            "imagem": None,
            "uid": None,
            "eventos": {}
        }

        eventos_tmp = {}
        lines = vcard.splitlines()

        for line in lines:
            line = line.strip()

            if line.startswith("FN:"):
                contato["nome_completo"] = line[3:].strip()

            elif line.startswith("N:"):
                partes = line[2:].split(";")
                contato["nome"] = partes[1].strip() if len(partes) > 1 else partes[0].strip()

            elif line.startswith("NICKNAME:"):
                contato["apelido"] = line[9:].strip()

            elif line.startswith("EMAIL"):
                parts = line.split(":")
                if len(parts) > 1:
                    contato["email"].append(parts[-1].strip())

            elif line.startswith("TEL"):
                parts = line.split(":")
                if len(parts) > 1:
                    contato["telefone"].append(parts[-1].strip())

            elif line.startswith("ORG:"):
                contato["empresa"] = line[4:].strip()

            elif line.startswith("TITLE:"):
                contato["cargo"] = line[6:].strip()

            elif "ADR" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    endereco = parts[-1].replace(";", " ").strip()
                    contato["endereco"].append(endereco)

            elif line.startswith("BDAY:"):
                contato["aniversario"] = line[5:].strip()

            elif line.startswith("NOTE:"):
                contato["notas"] = line[5:].strip()

            elif line.startswith("PHOTO") and "VALUE=uri:" in line:
                parts = line.split("VALUE=uri:")
                if len(parts) > 1:
                    contato["imagem"] = parts[-1].strip()

            elif line.startswith("UID:"):
                contato["uid"] = line[4:].strip()

            elif line.startswith("URL:"):
                contato["websites"].append(line[4:].strip())

            elif "X-ABLabel" in line and not re.match(r"item\d+\.X-ABLabel", line):
                label = line.split(":")[-1].strip()
                contato["tags"].append(label)

            elif "X-SOCIALPROFILE" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    url = parts[-1].strip()
                    if "linkedin.com" in url:
                        contato["linkedin"] = url
                    else:
                        tipo_match = re.search(r"type=([^;:]+)", line.lower())
                        tipo = tipo_match.group(1) if tipo_match else "outro"
                        contato["outras_redes"][tipo] = url

            elif re.match(r"item\d+\.X-ABDATE", line):
                item, date = line.split(":")
                eventos_tmp[item.replace(".X-ABDATE", "")] = date.strip()

            elif re.match(r"item\d+\.X-ABLabel", line):
                item, label = line.split(":")
                item_id = item.replace(".X-ABLabel", "")
                if item_id in eventos_tmp:
                    contato["eventos"][label.strip()] = eventos_tmp[item_id]

        contatos.append(contato)

    return contatos