import os
import requests
from requests.auth import HTTPBasicAuth

def get_contacts_raw():
    url = os.environ.get("CARD_DAV_URL")
    apple_id = os.environ.get("APPLE_ID")
    app_password = os.environ.get("APPLE_APP_PASSWORD")

    if not url or not apple_id or not app_password:
        return {"erro": "Variáveis de ambiente faltando."}

    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
    }

    body = """<?xml version="1.0" encoding="UTF-8"?>
<card:addressbook-query xmlns:card="urn:ietf:params:xml:ns:carddav"
                        xmlns:d="DAV:">
  <d:prop>
    <d:getetag/>
    <card:address-data/>
  </d:prop>
</card:addressbook-query>"""

    try:
        response = requests.request(
            method="REPORT",
            url=url,
            headers=headers,
            data=body.encode("utf-8"),
            auth=HTTPBasicAuth(apple_id, app_password)
        )

        print("=== DEBUG CARD_DAV REPORT ===")
        print("Request URL:", url)
        print("Status Code:", response.status_code)
        print("Response Headers:", response.headers)
        print("Response Body:", response.text[:1000])  # evita log gigante

        if response.status_code != 207:
            return {
                "erro": "Erro no REPORT",
                "status": response.status_code,
                "request_url": url,
                "request_headers": headers,
                "response_headers": dict(response.headers),
                "body": response.text
            }

        return response.text

    except Exception as e:
        return {"erro": str(e)}