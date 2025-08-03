import os
import requests
import base64
import vobject
from unidecode import unidecode

CARD_DAV_URL = os.getenv("CARD_DAV_URL")
APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")

def get_contacts_raw():
    if not CARD_DAV_URL:
        return {"erro": "CARD_DAV_URL não configurada"}

    xml_body = """<?xml version="1.0" encoding="UTF-8"?>
<C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
  <D:prop>
    <D:getetag/>
    <C:address-data/>
  </D:prop>
  <C:filter/>
</C:addressbook-query>
"""

    auth = f"{APPLE_ID}:{APPLE_APP_PASSWORD}"
    b64_auth = base64.b64encode(auth.encode()).decode()

    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
        "Authorization": f"Basic {b64_auth}",
    }

    try:
        response = requests.request(
            "REPORT",
            CARD_DAV_URL,
            headers=headers,
            data=xml_body.encode("utf-8"),
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

def parse_vcards(xml_data):
    import xml.etree.ElementTree as ET
    contatos = []

    try:
        root = ET.fromstring(xml_data)
        for resp in root.findall(".//{DAV:}response"):
            href = resp.find("{DAV:}href").text if resp.find("{DAV:}href") is not None else ""
            prop = resp.find("{DAV:}propstat/{DAV:}prop", {"DAV": "DAV:"})
            if prop is None:
                continue
            card = prop.find("{urn:ietf:params:xml:ns:carddav}address-data")
            if card is None or not card.text:
                continue
            try:
                vcard = vobject.readOne(card.text)
                contato = {}
                if hasattr(vcard, "fn"):
                    contato["nome"] = vcard.fn.value
                    contato["nome_normalizado"] = unidecode(vcard.fn.value.lower())
                if hasattr(vcard, "email"):
                    contato["email"] = vcard.email.value
                if hasattr(vcard, "tel"):
                    contato["telefone"] = vcard.tel.value
                if hasattr(vcard, "org"):
                    contato["empresa"] = ";".join(vcard.org.value)
                if hasattr(vcard, "title"):
                    contato["cargo"] = vcard.title.value
                if hasattr(vcard, "url"):
                    contato["linkedin"] = vcard.url.value if "linkedin.com" in vcard.url.value else None
                    contato["redes"] = vcard.url.value if "linkedin.com" not in vcard.url.value else None
                if hasattr(vcard, "note"):
                    contato["notas"] = vcard.note.value
                if hasattr(vcard, "bday"):
                    contato["aniversario"] = vcard.bday.value
                if hasattr(vcard, "adr"):
                    endereco = vcard.adr.value
                    contato["endereco"] = ", ".join(filter(None, [
                        endereco.street, endereco.city, endereco.region,
                        endereco.code, endereco.country
                    ]))
                contato["datas"] = []
                for c in vcard.contents.get("x-abdate", []):
                    contato["datas"].append({
                        "label": c.params.get("X-ABLABEL", [""])[0],
                        "data": c.value.isoformat() if hasattr(c.value, "isoformat") else str(c.value)
                    })
                contatos.append(contato)
            except Exception:
                continue
    except Exception as e:
        return [{"erro": f"Falha ao processar XML: {str(e)}"}]

    return contatos

def buscar_por_nome(nome, contatos):
    termo = unidecode(nome.lower())
    return [
        c for c in contatos
        if termo in c.get("nome_normalizado", "")
        or termo in c.get("email", "").lower()
        or termo in c.get("telefone", "")
    ]