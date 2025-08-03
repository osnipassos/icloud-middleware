import os
import re
import vobject
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.getenv("CARD_DAV_URL")

def normalizar_nome(nome):
    return re.sub(r'\W+', ' ', nome).strip().lower()

def get_contacts_raw():
    if not CARD_DAV_URL:
        return {"erro": "CARD_DAV_URL não configurada"}

    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
    }

    data = """<?xml version="1.0" encoding="UTF-8"?>
<card:addressbook-query xmlns:card="urn:ietf:params:xml:ns:carddav"
  xmlns:d="DAV:">
  <d:prop>
    <d:getetag/>
    <card:address-data/>
  </d:prop>
</card:addressbook-query>"""

    try:
        response = requests.request(
            "REPORT",
            CARD_DAV_URL,
            headers=headers,
            data=data.encode("utf-8"),
            auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD),
        )

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

    except Exception as e:
        return {"erro": str(e)}

def parse_vcards(multivcard):
    contatos = []
    if not multivcard:
        return contatos

    for vcard in vobject.readComponents(multivcard):
        contato = {}
        contato["nome"] = vcard.fn.value if hasattr(vcard, 'fn') else ""
        contato["nome_normalizado"] = normalizar_nome(contato["nome"])
        contato["email"] = vcard.email.value if hasattr(vcard, 'email') else ""
        contato["telefone"] = vcard.tel.value if hasattr(vcard, 'tel') else ""
        contato["empresa"] = vcard.org.value[0] if hasattr(vcard, 'org') else ""
        contato["cargo"] = vcard.title.value if hasattr(vcard, 'title') else ""
        contato["notas"] = vcard.note.value if hasattr(vcard, 'note') else ""
        contato["linkedin"] = None
        contato["redes"] = []

        if hasattr(vcard, 'url'):
            url_val = vcard.url.value
            if 'linkedin' in url_val:
                contato["linkedin"] = url_val
            else:
                contato["redes"].append(url_val)

        if hasattr(vcard, 'bday'):
            try:
                contato["aniversario"] = vcard.bday.value.isoformat()
            except Exception:
                contato["aniversario"] = vcard.bday.value

        if hasattr(vcard, 'adr'):
            try:
                adr = vcard.adr.value
                contato["endereco"] = " ".join(filter(None, [
                    adr.street, adr.city, adr.region, adr.code, adr.country
                ]))
            except Exception:
                contato["endereco"] = str(vcard.adr.value)

        contato["datas"] = []
        for attr in vcard.contents.get("x-abdate", []):
            try:
                data_str = attr.value
                data_formatada = datetime.strptime(data_str, "%Y-%m-%d").date().isoformat()
                label = attr.params.get("x-ablabel", [""])[0]
                contato["datas"].append({"label": label, "data": data_formatada})
            except Exception:
                continue

        contatos.append(contato)

    return contatos

def buscar_por_nome(vc_cards, termo):
    termo_normalizado = normalizar_nome(termo)
    contatos_filtrados = []

    for contato in parse_vcards(vc_cards):
        if termo_normalizado in contato["nome_normalizado"]:
            contatos_filtrados.append(contato)

    return contatos_filtrados