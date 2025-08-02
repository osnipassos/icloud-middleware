import requests
import re
from xml.etree import ElementTree as ET

ICLOUD_USERNAME = "seu_usuario@icloud.com"
ICLOUD_PASSWORD = "sua_senha_do_app"
ICLOUD_URL = "https://contacts.icloud.com"

HEADERS = {
    "Depth": "1",
    "Content-Type": "application/xml; charset=UTF-8"
}

def get_contacts_raw():
    url = f"{ICLOUD_URL}/275963685/carddavhome/card/"

    body = '''<?xml version="1.0" encoding="UTF-8"?>
<card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:prop>
    <d:getetag />
    <card:address-data />
  </d:prop>
</card:addressbook-query>'''

    response = requests.request(
        "REPORT",
        url,
        headers=HEADERS,
        data=body,
        auth=(ICLOUD_USERNAME, ICLOUD_PASSWORD)
    )

    if response.status_code != 207:
        raise Exception(f"Erro no REPORT: {response.status_code}", response.text)

    return response.text

def parse_vcards(multistatus_xml):
    ns = {
        'd': 'DAV:',
        'card': 'urn:ietf:params:xml:ns:carddav'
    }
    contatos = []
    root = ET.fromstring(multistatus_xml)
    for resp in root.findall('d:response', ns):
        vcard_data = resp.find('.//card:address-data', ns)
        if vcard_data is not None and vcard_data.text:
            vcard_text = vcard_data.text
            contato = {}
            contato["nome"] = _extrair_campo(vcard_text, "FN")
            contato["email"] = _extrair_campo(vcard_text, "EMAIL")
            contato["telefone"] = _extrair_campo(vcard_text, "TEL")
            contato["empresa"] = _extrair_campo(vcard_text, "ORG")
            contato["cargo"] = _extrair_campo(vcard_text, "TITLE")
            contato["linkedin"] = _extrair_linkedin(vcard_text)
            contatos.append(contato)
    return contatos

def _extrair_campo(vcard, campo):
    match = re.search(f"{campo}.*:(.+)", vcard)
    return match.group(1).strip() if match else None

def _extrair_linkedin(vcard):
    match = re.search(r"X-SOCIALPROFILE.*linkedin.*:(https://[^
\r]+)", vcard)
    return match.group(1).strip() if match else None