import os
import re
import requests
import vobject
from requests.auth import HTTPBasicAuth

APPLE_ID = os.environ.get("APPLE_ID")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.environ.get("CARD_DAV_URL")

def get_contacts_raw():
    if not CARD_DAV_URL:
        return {"erro": "CARD_DAV_URL não configurada"}

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<card:addressbook-query xmlns:card="urn:ietf:params:xml:ns:carddav">
  <prop xmlns="DAV:">
    <getetag/>
    <address-data/>
  </prop>
</card:addressbook-query>"""

    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1"
    }

    try:
        response = requests.request(
            "REPORT",
            CARD_DAV_URL,
            headers=headers,
            data=xml.encode("utf-8"),
            auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD),
        )
    except Exception as e:
        return {"erro": "Erro de conexão", "detalhes": str(e)}

    if response.status_code != 207:
        return {
            "erro": "Erro no REPORT",
            "status": response.status_code,
            "request_url": CARD_DAV_URL,
            "request_headers": headers,
            "response_headers": dict(response.headers),
            "body": response.text,
        }

    return response.text

def normalize_name(name):
    return re.sub(r"[^a-z0-9]", " ", name.lower())

def parse_vcards(xml):
    contatos = []
    vcards = re.findall(r"BEGIN:VCARD(.*?)END:VCARD", xml, re.DOTALL)

    for raw_vcard in vcards:
        vcard_str = f"BEGIN:VCARD{raw_vcard}END:VCARD"
        try:
            vcard = vobject.readOne(vcard_str)
        except Exception:
            continue

        contato = {}
        contato["nome"] = vcard.fn.value if hasattr(vcard, "fn") else None
        contato["nome_normalizado"] = normalize_name(contato["nome"]) if contato["nome"] else None

        if hasattr(vcard, "email"):
            contato["email"] = str(vcard.email.value)

        if hasattr(vcard, "tel"):
            contato["telefone"] = str(vcard.tel.value)

        if hasattr(vcard, "org"):
            contato["empresa"] = " ".join(vcard.org.value)

        if hasattr(vcard, "title"):
            contato["cargo"] = vcard.title.value

        if hasattr(vcard, "bday"):
            try:
                contato["aniversario"] = vcard.bday.value.isoformat()
            except Exception:
                contato["aniversario"] = str(vcard.bday.value)

        if hasattr(vcard, "adr"):
            endereco = vcard.adr.value
            parts = [endereco.street, endereco.city, endereco.region, endereco.code, endereco.country]
            contato["endereco"] = ", ".join([p for p in parts if p])

        if hasattr(vcard, "url"):
            contato["linkedin"] = vcard.url.value if "linkedin" in vcard.url.value else None
            contato["redes"] = vcard.url.value if "linkedin" not in vcard.url.value else None

        if hasattr(vcard, "note"):
            contato["notas"] = vcard.note.value

        datas = []
        for attr in vcard.contents.get("x-abdate", []):
            datas.append({
                "label": attr.params.get("x-ablabel", [""])[0],
                "data": attr.value
            })
        contato["datas"] = datas if datas else None

        contatos.append(contato)

    return contatos

def buscar_por_nome(nome, contatos):
    nome = normalize_name(nome)
    return [c for c in contatos if nome in c.get("nome_normalizado", "")]