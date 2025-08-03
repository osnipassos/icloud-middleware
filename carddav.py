import os
import requests
from dotenv import load_dotenv
from icalendar import Calendar
from vobject import readOne

load_dotenv()

APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.getenv("CARD_DAV_URL")
APPLE_CONTACTS_ID = os.getenv("APPLE_CONTACTS_ID")

def get_contacts_raw():
    url = f"{CARD_DAV_URL}/{APPLE_CONTACTS_ID}/card/"
    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1"
    }
    body = """<?xml version="1.0" encoding="UTF-8" ?>
<card:addressbook-query xmlns:card="urn:ietf:params:xml:ns:carddav"
                        xmlns:d="DAV:">
  <d:prop>
    <d:getetag/>
    <card:address-data/>
  </d:prop>
</card:addressbook-query>"""

    response = requests.request(
        "REPORT",
        url,
        headers=headers,
        data=body,
        auth=(APPLE_ID, APPLE_APP_PASSWORD)
    )

    if not response.ok:
        raise Exception({
            "erro": "Erro no REPORT",
            "status": response.status_code,
            "request_url": url,
            "request_headers": headers,
            "response_headers": dict(response.headers),
            "body": response.text
        })

    return response.text

def parse_vcards(response_text):
    import xml.etree.ElementTree as ET
    ns = {'d': 'DAV:', 'card': 'urn:ietf:params:xml:ns:carddav'}
    root = ET.fromstring(response_text)
    contatos = []

    for response in root.findall('d:response', ns):
        data = response.find('.//card:address-data', ns)
        if data is not None and data.text:
            try:
                vcard = readOne(data.text)
                contato = {
                    "nome": getattr(vcard, 'fn', None).value if hasattr(vcard, 'fn') else None,
                    "nome_normalizado": getattr(vcard, 'fn', None).value.lower() if hasattr(vcard, 'fn') else None,
                    "email": getattr(vcard, 'email', None).value if hasattr(vcard, 'email') else None,
                    "telefone": getattr(vcard, 'tel', None).value if hasattr(vcard, 'tel') else None,
                    "empresa": getattr(vcard, 'org', None).value[0] if hasattr(vcard, 'org') and vcard.org.value else None,
                    "cargo": getattr(vcard, 'title', None).value if hasattr(vcard, 'title') else None,
                    "aniversario": vcard.bday.value if hasattr(vcard, 'bday') else None,
                    "endereco": vcard.adr.value.to_string() if hasattr(vcard, 'adr') else None,
                    "linkedin": None,
                    "datas": [],
                }

                if hasattr(vcard, 'url') and vcard.url.value and 'linkedin.com' in vcard.url.value:
                    contato["linkedin"] = vcard.url.value

                for key in vcard.contents:
                    if key not in ['bday', 'url', 'version', 'prodid', 'fn', 'n', 'tel', 'email', 'org', 'title', 'adr']:
                        values = vcard.contents[key]
                        for val in values:
                            label = val.params.get('X-ABLABEL') or val.params.get('LABEL') or ''
                            data_str = str(val.value)
                            contato['datas'].append({"label": label, "data": data_str})

                contatos.append(contato)
            except Exception as e:
                print(f"Erro ao parsear vCard: {e}")
                continue

    return contatos

def buscar_por_nome(nome: str):
    raw = get_contacts_raw()
    contatos = parse_vcards(raw)
    nome_normalizado = nome.strip().lower()
    return [c for c in contatos if nome_normalizado in c["nome_normalizado"]]