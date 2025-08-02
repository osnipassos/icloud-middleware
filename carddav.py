import os
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

def get_contacts():
    try:
        auth = HTTPBasicAuth(os.getenv("APPLE_ID"), os.getenv("APPLE_APP_PASSWORD"))

        ns = {"d": "DAV:", "card": "urn:ietf:params:xml:ns:carddav"}

        # 1. Descobrir a URL principal
        url_base = "https://contacts.icloud.com/"
        headers = {"Depth": "0", "Content-Type": "application/xml"}
        body1 = """<?xml version="1.0" encoding="UTF-8"?>
        <propfind xmlns="DAV:">
          <prop>
            <current-user-principal/>
          </prop>
        </propfind>"""

        r1 = requests.request("PROPFIND", url_base, headers=headers, data=body1, auth=auth)
        if r1.status_code != 207:
            return [{"erro": "Erro no PROPFIND 1", "status": r1.status_code, "body": r1.text}]
        root1 = ET.fromstring(r1.text)
        principal_href = root1.find(".//d:current-user-principal/d:href", ns).text

        # 2. Fazer novo PROPFIND no /principal/ para descobrir o addressbook-home-set
        url_principal = f"https://contacts.icloud.com{principal_href}"
        headers["Depth"] = "0"
        body2 = """<?xml version="1.0" encoding="UTF-8"?>
        <propfind xmlns="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
          <prop>
            <card:addressbook-home-set/>
          </prop>
        </propfind>"""

        r2 = requests.request("PROPFIND", url_principal, headers=headers, data=body2, auth=auth)
        if r2.status_code != 207:
            return [{"erro": "Erro no PROPFIND 2", "status": r2.status_code, "body": r2.text}]
        root2 = ET.fromstring(r2.text)
        addressbook_home = root2.find(".//card:addressbook-home-set/d:href", ns).text

        # 3. Fazer novo PROPFIND no /carddavhome/ para descobrir a collection
        url_home = f"https://contacts.icloud.com{addressbook_home}"
        headers["Depth"] = "1"
        body3 = """<?xml version="1.0" encoding="UTF-8"?>
        <propfind xmlns="DAV:">
          <prop>
            <displayname/>
          </prop>
        </propfind>"""

        r3 = requests.request("PROPFIND", url_home, headers=headers, data=body3, auth=auth)
        if r3.status_code != 207:
            return [{"erro": "Erro no PROPFIND 3", "status": r3.status_code, "body": r3.text}]
        root3 = ET.fromstring(r3.text)
        collection_href = None
        for resp in root3.findall(".//d:response", ns):
            href = resp.find("d:href", ns).text
            if href and href != addressbook_home:
                collection_href = href
                break

        if not collection_href:
            return [{"erro": "Não encontrou collection do addressbook"}]

        # 4. Fazer REPORT na collection
        report_url = f"https://contacts.icloud.com{collection_href}"
        headers = {"Depth": "1", "Content-Type": "application/xml"}
        body4 = """<?xml version="1.0" encoding="UTF-8"?>
        <card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
          <d:prop>
            <d:getetag/>
            <card:address-data/>
          </d:prop>
        </card:addressbook-query>"""

        r4 = requests.request("REPORT", report_url, headers=headers, data=body4, auth=auth)
        if r4.status_code != 207:
            return [{"erro": "Erro no REPORT", "body": r4.text}]

        return [{"vcard_raw": r4.text}]

    except Exception as e:
        return [{"erro": f"Exceção inesperada: {str(e)}"}]