import os
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

def get_contacts():
    try:
        auth = HTTPBasicAuth(os.getenv("APPLE_ID"), os.getenv("APPLE_APP_PASSWORD"))

        # 1. Descobrir o principal
        propfind_url = "https://contacts.icloud.com/"
        headers = {
            "Depth": "0",
            "Content-Type": "application/xml"
        }
        body = """<?xml version="1.0" encoding="UTF-8"?>
        <propfind xmlns="DAV:">
          <prop>
            <current-user-principal/>
          </prop>
        </propfind>"""

        response = requests.request("PROPFIND", propfind_url, headers=headers, data=body, auth=auth)
        if response.status_code != 207:
            return [{"erro": "Erro no PROPFIND (descoberta)", "status": response.status_code, "body": response.text}]
        print("DISCOVERY STATUS:", response.status_code)
        print("DISCOVERY BODY:", response.text)

        root = ET.fromstring(response.text)
        ns = {"d": "DAV:"}
        principal_url = root.find(".//d:current-user-principal/d:href", ns).text

        # 2. Descobrir o addressbook
        propfind2_url = f"https://contacts.icloud.com{principal_url}"
        headers["Depth"] = "1"
        body2 = """<?xml version="1.0" encoding="UTF-8"?>
        <propfind xmlns="DAV:">
          <prop>
            <displayname/>
          </prop>
        </propfind>"""

        response2 = requests.request("PROPFIND", propfind2_url, headers=headers, data=body2, auth=auth)
        if response2.status_code != 207:
            return [{"erro": "Erro no PROPFIND (addressbook)", "status": response2.status_code, "body": response2.text}]
        print("CARDDAV STATUS:", response2.status_code)
        print("CARDDAV BODY:", response2.text)

        root2 = ET.fromstring(response2.text)
        responses = root2.findall(".//d:response", ns)
        addressbook_url = None

        for resp in responses:
            href = resp.find("d:href", ns)
            if href is not None and "/carddavhome/" in href.text:
                addressbook_url = href.text
                break

        if not addressbook_url:
            return [{"erro": "Não encontrou a URL do addressbook"}]

        # 3. Fazer REPORT
        report_url = f"https://contacts.icloud.com{addressbook_url}"
        headers = {
            "Depth": "1",
            "Content-Type": "application/xml"
        }
        body3 = """<?xml version="1.0" encoding="UTF-8"?>
        <card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
          <d:prop>
            <d:getetag/>
            <card:address-data/>
          </d:prop>
        </card:addressbook-query>"""

        response3 = requests.request("REPORT", report_url, headers=headers, data=body3, auth=auth)
        if response3.status_code != 207:
            return [{"erro": "Erro no REPORT", "body": response3.text}]

        return [{"vcard_raw": response3.text}]

    except Exception as e:
        return [{"erro": f"Exceção inesperada: {str(e)}"}]