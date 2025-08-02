import os
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

def get_contacts():
    try:
        auth = HTTPBasicAuth(os.getenv("APPLE_ID"), os.getenv("APPLE_APP_PASSWORD"))

        # 1. Descobrir URL principal
        principal_req = requests.request(
            "PROPFIND",
            "https://contacts.icloud.com/",
            headers={"Depth": "0", "Content-Type": "application/xml"},
            data="""<?xml version="1.0" encoding="utf-8" ?>
<propfind xmlns="DAV:">
  <prop>
    <current-user-principal />
  </prop>
</propfind>""",
            auth=auth,
        )

        principal_tree = ET.fromstring(principal_req.text)
        ns = {"D": "DAV:"}
        href_el = principal_tree.find(".//D:current-user-principal/D:href", ns)
        if href_el is None:
            return [{"erro": "Não encontrou current-user-principal"}]
        principal_url = href_el.text

        # 2. Descobrir addressbook-home-set
        home_req = requests.request(
            "PROPFIND",
            f"https://contacts.icloud.com{principal_url}",
            headers={"Depth": "0", "Content-Type": "application/xml"},
            data="""<?xml version="1.0" encoding="utf-8" ?>
<propfind xmlns="DAV:">
  <prop>
    <addressbook-home-set xmlns="urn:ietf:params:xml:ns:carddav"/>
  </prop>
</propfind>""",
            auth=auth,
        )

        home_tree = ET.fromstring(home_req.text)
        href_el = home_tree.find(".//{urn:ietf:params:xml:ns:carddav}addressbook-home-set/{DAV:}href")
        if href_el is None:
            return [{"erro": "Não encontrou a URL do addressbook", "respostas": [principal_url]}]

        home_url = href_el.text

        # Corrigir erro de concatenação da URL
        if home_url.startswith("http"):
            collection_url = home_url
        else:
            collection_url = f"https://contacts.icloud.com{home_url}"

        # 3. REPORT para obter os contatos
        report_req = requests.request(
            "REPORT",
            collection_url,
            headers={"Depth": "1", "Content-Type": "application/xml"},
            data="""<?xml version="1.0" encoding="utf-8" ?>
<card:addressbook-query xmlns:card="urn:ietf:params:xml:ns:carddav">
  <prop xmlns="DAV:">
    <getetag/>
    <address-data xmlns="urn:ietf:params:xml:ns:carddav"/>
  </prop>
</card:addressbook-query>""",
            auth=auth,
        )

        if report_req.status_code != 207:
            return [{"erro": "Erro no REPORT", "body": report_req.text}]

        return [{"vcard": report_req.text}]

    except Exception as e:
        return [{"erro": f"Exceção inesperada: {e}"}]