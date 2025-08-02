import os
import requests
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth

APPLE_ID = os.environ.get("APPLE_ID")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD")
APPLE_CONTACTS_HOST = os.environ.get("APPLE_CONTACTS_HOST", "p42-contacts.icloud.com")
APPLE_CONTACTS_ID = os.environ.get("APPLE_CONTACTS_ID")

CARD_DAV_URL = f"https://{APPLE_CONTACTS_HOST}/{APPLE_CONTACTS_ID}/carddavhome/"

HEADERS = {
    "Depth": "1",
    "Content-Type": "application/xml; charset=utf-8"
}

REPORT_BODY = '''
<card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:prop>
    <d:getetag />
    <card:address-data />
  </d:prop>
</card:addressbook-query>
'''

def get_contacts_raw():
    try:
        response = requests.request(
            "REPORT",
            CARD_DAV_URL,
            headers=HEADERS,
            data=REPORT_BODY,
            auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD)
        )

        if response.status_code != 207:
            return {"erro": "Erro no REPORT", "status": response.status_code, "body": response.text}

        return {"vcard": response.text}
    except Exception as e:
        return {"erro": f"Exceção inesperada: {str(e)}"}

def parse_vcards(xml_content):
    contatos = []
    ns = {
        'd': 'DAV:',
        'card': 'urn:ietf:params:xml:ns:carddav'
    }

    try:
        root = ET.fromstring(xml_content)
        for response in root.findall('d:response', ns):
            contato = {
                "nome": None,
                "nome_completo": None,
                "email": None,
                "telefone": None,
                "empresa": None,
                "cargo": None,
                "linkedin": None,
                "facebook": None,
                "skype": None,
                "enderecos": [],
                "datas": [],
                "tags": [],
                "foto": None,
                "site": None
            }

            vcard_elem = response.find(".//card:address-data", ns)
            if vcard_elem is not None and vcard_elem.text:
                vcard = vcard_elem.text.replace("\r\n", "\n").split("\n")
                for line in vcard:
                    if line.startswith("FN:"):
                        contato["nome_completo"] = line[3:]
                    elif line.startswith("N:"):
                        partes = line[2:].split(";")
                        contato["nome"] = " ".join([p for p in partes if p])
                    elif line.startswith("EMAIL"):
                        contato["email"] = line.split(":")[-1]
                    elif line.startswith("TEL"):
                        contato["telefone"] = line.split(":")[-1]
                    elif line.startswith("ORG:"):
                        contato["empresa"] = line[4:]
                    elif line.startswith("TITLE:"):
                        contato["cargo"] = line[6:]
                    elif "linkedin.com/in" in line:
                        contato["linkedin"] = line.split(":")[-1]
                    elif "facebook.com" in line:
                        contato["facebook"] = line.split(":")[-1]
                    elif "skype" in line.lower():
                        contato["skype"] = line.split(":")[-1]
                    elif line.startswith("item") and ".ADR" in line:
                        contato["enderecos"].append(line.split(":")[-1])
                    elif line.startswith("item") and ".X-ABDATE" in line:
                        contato["datas"].append(line.split(":")[-1])
                    elif line.startswith("item") and ".X-ABLabel" in line:
                        contato["tags"].append(line.split(":")[-1])
                    elif line.startswith("PHOTO") and "uri:" in line:
                        contato["foto"] = line.split("uri:")[-1]
                    elif line.startswith("URL:"):
                        contato["site"] = line[4:]

                if contato["nome"] is None:
                    contato["nome"] = contato["nome_completo"]

                contatos.append(contato)
    except Exception as e:
        contatos.append({"erro": f"Erro no parse: {str(e)}"})

    return contatos