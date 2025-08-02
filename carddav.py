import requests
from requests.auth import HTTPBasicAuth
import os
import xml.etree.ElementTree as ET
import re

def get_contacts():
    try:
        auth = HTTPBasicAuth(os.getenv("APPLE_ID"), os.getenv("APPLE_APP_PASSWORD"))
        base_url = "https://contacts.icloud.com"
        headers = {
            "Depth": "1",
            "Content-Type": "application/xml"
        }

        # Etapa 1 – Descobre a URL do usuário (current-user-principal)
        discovery_body = """
        <d:propfind xmlns:d="DAV:">
            <d:prop>
                <d:current-user-principal />
            </d:prop>
        </d:propfind>
        """
        discovery_resp = requests.request("PROPFIND", base_url + "/", headers=headers, data=discovery_body, auth=auth)
        if discovery_resp.status_code != 207:
            return [{"erro": f"Erro no discovery: {discovery_resp.status_code}"}]

        tree = ET.fromstring(discovery_resp.text)
        ns = {'d': 'DAV:'}
        user_href = tree.find('.//d:current-user-principal/d:href', ns)
        if user_href is None:
            return [{"erro": "current-user-principal não encontrado"}]
        user_url = f"{base_url}{user_href.text}"

        # Etapa 2 – Descobre a addressbook
        addressbook_body = """
        <d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
            <d:prop>
                <d:displayname />
            </d:prop>
        </d:propfind>
        """
        addressbook_resp = requests.request("PROPFIND", user_url, headers=headers, data=addressbook_body, auth=auth)
        if addressbook_resp.status_code != 207:
            return [{"erro": f"Erro no addressbook: {addressbook_resp.status_code}"}]

        tree = ET.fromstring(addressbook_resp.text)
        hrefs = tree.findall('.//d:response/d:href', ns)
        if not hrefs:
            return [{"erro": "Nenhum addressbook encontrado"}]

        addressbook_path = hrefs[0].text
        full_addressbook_url = f"{base_url}{addressbook_path}"

        # Etapa 3 – REPORT para buscar os contatos
        report_body = """<?xml version="1.0" encoding="UTF-8"?>
<card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:prop>
    <d:getetag/>
    <card:address-data>
      <card:prop name="FN"/>
      <card:prop name="TEL"/>
    </card:address-data>
  </d:prop>
</card:addressbook-query>
"""
        headers["Depth"] = "1"
        headers["Content-Type"] = "application/xml"
        report_resp = requests.request("REPORT", full_addressbook_url, headers=headers, data=report_body, auth=auth)
        if report_resp.status_code != 207:
            return [{"erro": f"Erro no REPORT: {report_resp.status_code}"}]

        # Etapa 4 – Parse dos vCards
        cards = re.findall(r'BEGIN:VCARD.*?END:VCARD', report_resp.text, re.DOTALL)
        contatos = []
        for card in cards:
            nome_match = re.search(r'FN:(.+)', card)
            tel_match = re.findall(r'TEL[^:]*:(\+?\d+)', card)
            nome = nome_match.group(1).strip() if nome_match else "Sem nome"
            telefones = ', '.join(tel_match) if tel_match else "Sem telefone"
            contatos.append({"nome": nome, "telefone": telefones})

        return contatos or [{"mensagem": "Nenhum contato encontrado"}]

    except Exception as e:
        return [{"erro": f"Exceção inesperada: {str(e)}"}]