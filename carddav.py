import os
import requests
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth

APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
AUTH = HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD)
HEADERS_XML = {"Depth": "1", "Content-Type": "application/xml"}
CARDDAV_URL = "https://contacts.icloud.com"

def propfind(url, xml_body):
    return requests.request("PROPFIND", url, headers=HEADERS_XML, data=xml_body, auth=AUTH)

def report(url, xml_body):
    return requests.request("REPORT", url, headers=HEADERS_XML, data=xml_body, auth=AUTH)

def get_contacts():
    try:
        # 1. Descobrir o principal
        body_principal = '''<?xml version="1.0" encoding="UTF-8"?>
        <d:propfind xmlns:d="DAV:">
            <d:prop>
                <d:current-user-principal/>
            </d:prop>
        </d:propfind>'''
        r1 = propfind(f"{CARDDAV_URL}/", body_principal)
        tree1 = ET.fromstring(r1.text)
        principal = tree1.find(".//{DAV:}href")
        if principal is None:
            return [{"erro": "Não encontrou o principal"}]
        principal_path = principal.text

        # 2. Descobrir o carddavhome
        body_home = '''<?xml version="1.0" encoding="UTF-8"?>
        <d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
            <d:prop>
                <cs:addressbook-home-set/>
            </d:prop>
        </d:propfind>'''
        r2 = propfind(f"{CARDDAV_URL}{principal_path}", body_home)
        tree2 = ET.fromstring(r2.text)
        home = tree2.find(".//{DAV:}href")
        if home is None:
            return [{"erro": "Não encontrou o carddavhome"}]
        home_path = home.text

        # 3. Listar todos os possíveis hrefs (para debug)
        body_list = '''<?xml version="1.0" encoding="UTF-8"?>
        <d:propfind xmlns:d="DAV:" xmlns:cd="urn:ietf:params:xml:ns:carddav">
            <d:prop>
                <d:displayname/>
                <cd:addressbook-description/>
            </d:prop>
        </d:propfind>'''
        r3 = propfind(f"{CARDDAV_URL}{home_path}", body_list)
        tree3 = ET.fromstring(r3.text)
        responses = tree3.findall(".//{DAV:}response")

        all_paths = []
        for resp in responses:
            href = resp.find("{DAV:}href")
            if href is not None:
                all_paths.append(href.text)

        # se não achou nenhum path que não seja "/", retorna lista para debug
        valid_paths = [p for p in all_paths if p and p != "/"]
        if not valid_paths:
            return [{"erro": "Não encontrou a URL do addressbook", "respostas": all_paths}]

        addressbook_path = valid_paths[0]

        # 4. Buscar VCards
        body_report = '''<?xml version="1.0" encoding="UTF-8"?>
        <card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
            <d:prop>
                <d:getetag/>
                <card:address-data/>
            </d:prop>
        </card:addressbook-query>'''
        r4 = report(f"{CARDDAV_URL}{addressbook_path}", body_report)

        if r4.status_code != 207:
            return [{"erro": "Erro no REPORT", "status": r4.status_code, "body": r4.text}]

        tree4 = ET.fromstring(r4.text)
        vcards = tree4.findall(".//{urn:ietf:params:xml:ns:carddav}address-data")
        contatos = [{"vcard": v.text} for v in vcards if v.text]
        return contatos if contatos else [{"erro": "Nenhum contato encontrado"}]

    except Exception as e:
        return [{"erro": f"Exceção inesperada: {e}"}]