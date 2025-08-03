import os
import requests
import vobject
from requests.auth import HTTPBasicAuth
from unidecode import unidecode
from dotenv import load_dotenv

load_dotenv()

APPLE_ID = os.environ.get("APPLE_ID")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.environ.get("CARD_DAV_URL")

def get_contacts_raw():
    if not CARD_DAV_URL:
        return {"erro": "CARD_DAV_URL não configurada"}

    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
    }

    body = """<?xml version="1.0" encoding="utf-8" ?>
    <C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
      <D:prop>
        <D:getetag/>
        <C:address-data/>
      </D:prop>
      <C:filter/>
    </C:addressbook-query>
    """

    response = requests.request(
        method="REPORT",
        url=CARD_DAV_URL,
        headers=headers,
        data=body.encode("utf-8"),
        auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD)
    )

    if response.status_code != 207:
        return {
            "erro": "Erro no REPORT",
            "status": response.status_code,
            "request_url": CARD_DAV_URL,
            "request_headers": headers,
            "response_headers": dict(response.headers),
            "body": response.text
        }

    return response.text

def normalize_nome(nome):
    return unidecode(nome.lower().strip())

def parse_vcards(xml_response):
    import xml.etree.ElementTree as ET
    contatos = []

    root = ET.fromstring(xml_response)
    ns = {"d": "DAV:", "c": "urn:ietf:params:xml:ns:carddav"}

    for response in root.findall("d:response", ns):
        vcard_data = response.find(".//c:address-data", ns)
        if vcard_data is None or not vcard_data.text:
            continue
        try:
            vcard = vobject.readOne(vcard_data.text)
        except Exception:
            continue

        contato = {}

        if hasattr(vcard, "fn"):
            contato["nome"] = vcard.fn.value
            contato["nome_normalizado"] = normalize_nome(vcard.fn.value)

        if hasattr(vcard, "email"):
            contato["email"] = vcard.email.value

        if hasattr(vcard, "tel"):
            contato["telefone"] = vcard.tel.value

        if hasattr(vcard, "org"):
            contato["empresa"] = " ".join(vcard.org.value)

        if hasattr(vcard, "title"):
            contato["cargo"] = vcard.title.value

        if hasattr(vcard, "bday"):
            contato["aniversario"] = (
                vcard.bday.value.isoformat()
                if hasattr(vcard.bday.value, "isoformat")
                else vcard.bday.value
            )

        if hasattr(vcard, "adr"):
            endereco = vcard.adr.value
            contato["endereco"] = " ".join([
                endereco.street or "",
                endereco.city or "",
                endereco.region or "",
                endereco.code or "",
                endereco.country or ""
            ]).strip()

        if hasattr(vcard, "url"):
            contato["linkedin"] = vcard.url.value
        else:
            contato["linkedin"] = None

        # Custom data (e.g. redes, datas)
        datas = []
        for prop in vcard.contents.get("x-abdate", []):
            datas.append({
                "label": prop.params.get("x-ablabel", [""])[0],
                "data": prop.value
            })
        contato["datas"] = datas if datas else None

        if hasattr(vcard, "note"):
            contato["notas"] = vcard.note.value

        contatos.append(contato)

    return contatos

def buscar_por_nome(nome, contatos):
    nome_normalizado = normalize_nome(nome)
    return [
        c for c in contatos
        if nome_normalizado in c.get("nome_normalizado", "")
           or nome_normalizado in normalize_nome(c.get("email", ""))
           or nome_normalizado in normalize_nome(c.get("telefone", ""))
    ]