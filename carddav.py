import os
import requests
import re
import vobject
from unidecode import unidecode
from datetime import datetime


def get_contacts_raw():
    url = os.environ.get("CARD_DAV_URL")
    if not url:
        return {"erro": "CARD_DAV_URL não configurada"}

    auth = (os.environ.get("APPLE_ID"), os.environ.get("APPLE_APP_PASSWORD"))
    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
    }
    body = """<?xml version="1.0" encoding="utf-8" ?>
    <A:propfind xmlns:A="DAV:">
      <A:prop>
        <A:getetag/>
        <A:getcontenttype/>
      </A:prop>
    </A:propfind>"""

    try:
        response = requests.request("REPORT", url, data=body, headers=headers, auth=auth)
        if response.status_code != 207:
            return {
                "erro": "Erro no REPORT",
                "status": response.status_code,
                "request_url": url,
                "request_headers": headers,
                "response_headers": dict(response.headers),
                "body": response.text
            }

        urls = re.findall(r"https?://[^\s\"']+", response.text)
        vcards = []
        for u in urls:
            if u.endswith(".vcf"):
                vcard_resp = requests.get(u, auth=auth)
                if vcard_resp.status_code == 200:
                    vcards.append(vcard_resp.text)
        return vcards
    except Exception as e:
        return {"erro": str(e)}


def parse_vcards(vcards):
    contatos = []

    for vcard_text in vcards:
        try:
            vcard = vobject.readOne(vcard_text)
            contato = {}

            # Nome
            if hasattr(vcard, "fn"):
                contato["nome"] = vcard.fn.value
                contato["nome_normalizado"] = unidecode(vcard.fn.value.lower())

            # Telefones
            if hasattr(vcard, "tel_list") and vcard.tel_list:
                contato["telefone"] = vcard.tel_list[0].value

            # Email
            if hasattr(vcard, "email_list") and vcard.email_list:
                contato["email"] = vcard.email_list[0].value

            # Empresa e cargo
            if hasattr(vcard, "org"):
                contato["empresa"] = vcard.org.value[0]
            if hasattr(vcard, "title"):
                contato["cargo"] = vcard.title.value

            # Endereço
            if hasattr(vcard, "adr_list") and vcard.adr_list:
                adr = vcard.adr_list[0]
                endereco = ", ".join(filter(None, [
                    adr.street, adr.city, adr.region, adr.code, adr.country
                ]))
                contato["endereco"] = endereco

            # Aniversário
            if hasattr(vcard, "bday"):
                contato["aniversario"] = vcard.bday.value.isoformat()

            # Notas
            if hasattr(vcard, "note"):
                contato["notas"] = vcard.note.value

            # Redes sociais (heurística via notas ou campos X-)
            redes = []
            linkedin = None
            for line in vcard_text.splitlines():
                if "linkedin.com/in/" in line:
                    linkedin = re.search(r"https?://[^\s]+", line)
                    if linkedin:
                        linkedin = linkedin.group(0)
                if "instagram.com" in line or "twitter.com" in line or "facebook.com" in line:
                    match = re.search(r"https?://[^\s]+", line)
                    if match:
                        redes.append(match.group(0))

            if linkedin:
                contato["linkedin"] = linkedin
            if redes:
                contato["redes"] = redes

            # Datas (X-APPLE-ABDATE, X-ANNIVERSARY, etc.)
            datas = []
            for line in vcard_text.splitlines():
                if ":" in line and any(k in line for k in ["BDAY", "ANNIVERSARY", "X-ABDATE", "X-APPLE-ABDATE"]):
                    try:
                        label, data = line.split(":", 1)
                        data = data.strip()
                        if re.match(r"^\d{4}-\d{2}-\d{2}$", data):
                            datas.append({"label": label.strip(), "data": data})
                    except Exception:
                        pass
            if datas:
                contato["datas"] = datas

            contatos.append(contato)

        except Exception as e:
            contatos.append({"erro": str(e)})

    return contatos


def buscar_por_nome(nome_parcial, contatos):
    termo = unidecode(nome_parcial.lower())
    resultados = []
    for contato in contatos:
        nome_normalizado = contato.get("nome_normalizado", "")
        if termo in nome_normalizado or any(termo in t for t in nome_normalizado.split()):
            resultados.append(contato)
    return resultados