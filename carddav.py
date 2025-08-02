import os
import requests
from requests.auth import HTTPBasicAuth
import re

def parse_vcard(vcard_text):
    contato = {}

    # Nome completo
    fn_match = re.search(r'FN:(.+)', vcard_text)
    if fn_match:
        contato["nome"] = fn_match.group(1).strip()

    # Telefone
    tel_match = re.search(r'TEL[^:]*:(.+)', vcard_text)
    if tel_match:
        contato["telefone"] = tel_match.group(1).strip()

    # Email
    email_match = re.search(r'EMAIL[^:]*:(.+)', vcard_text)
    if email_match:
        contato["email"] = email_match.group(1).strip()

    # Empresa (ORG)
    org_match = re.search(r'ORG:(.+)', vcard_text)
    if org_match:
        contato["empresa"] = org_match.group(1).strip().replace(";", "")

    # Cargo (TITLE)
    title_match = re.search(r'TITLE:(.+)', vcard_text)
    if title_match:
        contato["cargo"] = title_match.group(1).strip()

    # LinkedIn (X-SOCIALPROFILE)
    linkedin_match = re.search(r'X-SOCIALPROFILE[^:]*linkedin.*:(https?://[^\r\n]+)', vcard_text)
    if linkedin_match:
        contato["linkedin"] = linkedin_match.group(1).strip()

    return contato

def get_contacts():
    try:
        APPLE_ID = os.getenv("APPLE_ID")
        APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
        auth = HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD)

        base_url = "https://p42-contacts.icloud.com"
        addressbook_path = "/275963685/carddavhome/card/"
        url = f"{base_url}{addressbook_path}"

        headers = {
            "Depth": "1",
            "Content-Type": "application/xml; charset=utf-8"
        }

        body = """<?xml version="1.0" encoding="UTF-8"?>
        <card:addressbook-query xmlns:card="urn:ietf:params:xml:ns:carddav"
                                xmlns:d="DAV:">
          <d:prop>
            <d:getetag/>
            <card:address-data/>
          </d:prop>
        </card:addressbook-query>"""

        response = requests.request("REPORT", url, headers=headers, data=body, auth=auth)

        if response.status_code != 207:
            return [{"erro": "Erro no REPORT", "status": response.status_code, "body": response.text}]

        vcards = re.findall(r'BEGIN:VCARD(.*?)END:VCARD', response.text, re.DOTALL)
        contatos = [parse_vcard("BEGIN:VCARD" + v + "END:VCARD") for v in vcards]
        contatos = [c for c in contatos if c]  # remove vazios
        return contatos if contatos else [{"erro": "Nenhum contato válido encontrado"}]

    except Exception as e:
        return [{"erro": f"Exceção inesperada: {str(e)}"}]