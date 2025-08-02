import os
import requests
from requests.auth import HTTPBasicAuth

def get_contacts():
    try:
        APPLE_ID = os.getenv("APPLE_ID")
        APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
        auth = HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD)

        # 👇 Tente manualmente com o número do servidor "p42"
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

        return [{"vcard": response.text}]

    except Exception as e:
        return [{"erro": f"Exceção inesperada: {str(e)}"}]