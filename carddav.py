import os
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

def get_contacts():
    try:
        auth = HTTPBasicAuth(os.getenv("APPLE_ID"), os.getenv("APPLE_APP_PASSWORD"))

        # Etapa 1 – Discover principal URL
        discover_url = "https://contacts.icloud.com/"
        discover_body = """<?xml version="1.0" encoding="UTF-8"?>
        <d:propfind xmlns:d="DAV:">
          <d:prop>
            <d:current-user-principal/>
          </d:prop>
        </d:propfind>
        """
        headers = {"Content-Type": "application/xml"}
        r = requests.request("PROPFIND", discover_url, headers=headers, data=discover_body, auth=auth)

        print("DISCOVERY STATUS:", r.status_code)
        print("DISCOVERY BODY:", r.text)

        if r.status_code != 207:
            return [{"erro": "Erro no PROPFIND"}]

        root = ET.fromstring(r.text)
        ns = {"d": "DAV:"}
        principal_url = root.find(".//d:current-user-principal/d:href", ns).text

        # Etapa 2 – Discover address book URL
        abook_url = f"https://contacts.icloud.com{principal_url}"
        abook_body = """<?xml version="1.0" encoding="UTF-8"?>
        <d:propfind xmlns:d="DAV:">
          <d:prop>
            <d:displayname/>
          </d:prop>
        </d:propfind>
        """
        r2 = requests.request("PROPFIND", abook_url, headers=headers, data=abook_body, auth=auth)
        print("CARDDAV STATUS:", r2.status_code)
        print("CARDDAV BODY:", r2.text)

        if r2.status_code != 207:
            return [{"erro": "Erro no addressbook PROPFIND"}]

        root2 = ET.fromstring(r2.text)
        addressbook_url = root2.find(".//d:response/d:href", ns).text
        report_url = f"https://contacts.icloud.com{addressbook_url}"  # corrigido

        # Etapa 3 – REPORT para buscar os contatos
        report_body = """<?xml version="1.0" encoding="UTF-8"?>
        <card:addressbook-query xmlns:card="urn:ietf:params:xml:ns:carddav" xmlns:d="DAV:">
          <d:prop>
            <card:address-data>
              <card:prop name="FN"/>
              <card:prop name="TEL"/>
            </card:address-data>
          </d:prop>
        </card:addressbook-query>
        """

        r3 = requests.request("REPORT", report_url, headers=headers, data=report_body, auth=auth)
        print("REPORT STATUS:", r3.status_code)
        print("REPORT BODY:", r3.text[:500])  # Mostra só o começo

        if r3.status_code != 207:
            return [{"erro": "Erro no REPORT", "body": r3.text}]

        # Aqui você pode continuar o parsing se quiser extrair FN/TEL dos vCards

        return [{"status": "OK", "dados": r3.text}]

    except Exception as e:
        return [{"erro": f"Exceção inesperada: {e}"}]