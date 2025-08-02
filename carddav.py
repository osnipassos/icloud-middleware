import os
import requests
import xml.etree.ElementTree as ET
import re
from unidecode import unidecode

APPLE_ID = os.environ.get("APPLE_ID")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.environ.get("CARD_DAV_URL")

def normalize(text):
    if not text:
        return ""
    return unidecode(text).lower().strip()

def get_contacts_raw():
    try:
        auth = (APPLE_ID, APPLE_APP_PASSWORD)
        session = requests.Session()
        session.auth = auth

        if not CARD_DAV_URL:
            return {"erro": "CARD_DAV_URL não configurada"}

        report_body = """<?xml version="1.0" encoding="UTF-8"?>
<C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
  <D:prop>
    <D:getetag/>
    <C:address-data/>
  </D:prop>
</C:addressbook-query>
"""

        headers = {
            "Content-Type": "application/xml; charset=utf-8",
            "Depth": "1"
        }

        response = session.request(
            "REPORT",
            CARD_DAV_URL,
            data=report_body.encode("utf-8"),
            headers=headers
        )

        debug_info = {
            "status": response.status_code,
            "request_url": response.url,
            "request_headers": dict(response.request.headers),
            "response_headers": dict(response.headers),
            "body": response.text
        }

        if response.status_code != 207:
            return {"erro": "Erro no REPORT", **debug_info}

        return {"vcard": response.text}

    except Exception as e:
        return {"erro": f"Exceção inesperada: {str(e)}"}

def parse_vcards(xml_text):
    ns = {
        "D": "DAV:",
        "C": "urn:ietf:params:xml:ns:carddav"
    }
    root = ET.fromstring(xml_text)
    contatos = []
    for response in root.findall("D:response", ns):
        vcard_el = response.find("D:propstat/D:prop/C:address-data", ns)
        if vcard_el is not None:
            vcard = vcard_el.text or ""
            contato = parse_single_vcard(vcard)
            if contato:
                contatos.append(contato)
    return contatos

def parse_single_vcard(vcard):
    contato = {}
    lines = vcard.split("\n")
    datas = []
    redes = []

    for line in lines:
        line = line.strip()
        if line.startswith("FN:"):
            contato["nome"] = line[3:].strip()
            contato["nome_normalizado"] = normalize(contato["nome"])
        elif line.startswith("EMAIL"):
            email = line.split(":", 1)[1].strip()
            contato["email"] = email
        elif line.startswith("TEL"):
            telefone = line.split(":", 1)[1].strip()
            contato["telefone"] = telefone
        elif line.startswith("ORG:"):
            contato["empresa"] = line[4:].strip()
        elif line.startswith("TITLE:"):
            contato["cargo"] = line[6:].strip()
        elif line.startswith("X-SOCIALPROFILE"):
            match = re.search(r'https?://[^"\s]+', line)
            if match:
                url = match.group(0)
                redes.append(url)
        elif ".X-ABDATE" in line:
            data = line.split(":", 1)[1].strip()
            datas.append({"data": data})
        elif ".X-ABLabel:" in line:
            if datas:
                datas[-1]["label"] = line.split(":", 1)[1].strip()

    if redes:
        for url in redes:
            if "linkedin.com" in url:
                contato["linkedin"] = url
            elif "facebook.com" in url:
                contato["facebook"] = url
            elif "skype.com" in url:
                contato["skype"] = url

    if datas:
        contato["datas"] = datas

    return contato