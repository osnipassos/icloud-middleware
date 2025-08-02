import requests
from requests.auth import HTTPBasicAuth
import os
import xml.etree.ElementTree as ET
import re

def get_contacts():
    auth = HTTPBasicAuth(os.getenv("APPLE_ID"), os.getenv("APPLE_APP_PASSWORD"))
    base_url = "https://contacts.icloud.com"
    headers = {
        "Depth": "1",
        "Content-Type": "application/xml"
    }

    # Fase 1 – Descobre a URL principal do usuário
    discovery_body = """
    <d:propfind xmlns:d="DAV:">
        <d:prop>
            <d:current-user-principal />
        </d:prop>
    </d:propfind>
    """
    discovery_resp = requests.request("PROPFIND", base_url + "/", headers=headers, data=discovery_body, auth=auth)
    if discovery_resp.status_code != 207:
        return [f"Discovery error {discovery_resp.status_code}: {discovery_resp.text}"]

    tree = ET.fromstring(discovery_resp.text)
    ns = {'d': 'DAV:'}
    user_href = tree.find('.//d:current-user-principal/d:href', ns)
    if user_href is None:
        return ["Erro: não achou o href do principal"]
    user_url = base_url + user_href.text.strip('/')

    # Fase 2 – Descobre o endereço da agenda (addressbook)
    addressbook_body = """
    <d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
        <d:prop>
            <d:displayname />
        </d:prop>
    </d:propfind>
    """
    addressbook_resp = requests.request("PROPFIND", user_url + "/", headers=headers, data=addressbook_body, auth=auth)
    if addressbook_resp.status_code != 207:
        return [f"Addressbook error {addressbook_resp.status_code}: {addressbook_resp.text}"]

    tree = ET.fromstring(addressbook_resp.text)
    hrefs = tree.findall('.//d:response/d:href', ns)
    if not hrefs:
        return ["Nenhum addressbook encontrado"]

    # Usa o primeiro addressbook encontrado
    addressbook_path = hrefs[0].text
    full_addressbook_url = base_url + addressbook_path

    # Fase 3 – REPORT para pegar os vCards dos contatos
    report_body = """
    <c:addressbook-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav">
        <d:prop>
            <d:getetag />
            <c:address-data />
        </d:prop>
    </c:addressbook-query>
    """
    headers["Depth"] = "1"
    report_resp = requests.request("REPORT", full_addressbook_url, headers=headers, data=report_body, auth=auth)
    if report_resp.status_code != 207:
        return [f"Erro no REPORT {report_resp.status_code}: {report_resp.text}"]

    # Fase 4 – Extrai os dados dos vCards (nome e telefone)
    cards = re.findall(r'BEGIN:VCARD.*?END:VCARD', report_resp.text, re.DOTALL)
    contatos = []
    for card in cards:
        nome_match = re.search(r'FN:(.+)', card)
        tel_match = re.findall(r'TEL[^:]*:(\+?\d+)', card)
        nome = nome_match.group(1).strip() if nome_match else "Sem nome"
        telefones = ', '.join(tel_match) if tel_match else "Sem telefone"
        contatos.append({"nome": nome, "telefone": telefones})

    return contatos or ["Nenhum contato encontrado"]