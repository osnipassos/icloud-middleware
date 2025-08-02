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

        # Etapa 1: Descobre o current-user-principal
        discovery_body = """
        <d:propfind xmlns:d="DAV:">
            <d:prop>
                <d:current-user-principal />
            </d:prop>
        </d:propfind>
        """
        r1 = requests.request("PROPFIND", f"{base_url}/", headers=headers, data=discovery_body, auth=auth)
        if r1.status_code != 207:
            return [{"erro": f"Erro no discovery: {r1.status_code}"}]

        tree = ET.fromstring(r1.text)
        ns = {'d': 'DAV:'}
        user_href = tree.find('.//d:current-user-principal/d:href', ns)
        if user_href is None:
            return [{"erro": "current-user-principal não encontrado"}]
        user_path = user_href.text

        # Etapa 2: Descobre o addressbook-home-set
        propfind_body = """
        <d:propfind xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
          <d:prop>
            <card:addressbook-home-set />
          </d:prop>
        </d:propfind>
        """
        r2 = requests.request("PROPFIND", f"{base_url}{user_path}", headers=headers, data=propfind_body, auth=auth)
        if r2.status_code != 207:
            return [{"erro": f"Erro ao buscar addressbook-home-set: {r2.status_code}"}]

        tree = ET.fromstring(r2.text)
        home_href = tree.find('.//card:addressbook-home-set/d:href', {'card': 'urn:ietf:params:xml:ns:carddav', 'd': 'DAV:'})
        if home_href is None:
            return [{"erro": "addressbook-home-set não encontrado"}]
        addressbook_home = home_href.text

        # Etapa 3: Descobre o caminho completo do addressbook
        r3 = requests.request("PROPFIND", f"{base_url}{addressbook_home}", headers=headers, data="""
        <d:propfind xmlns:d="DAV:">
          <d:prop>
            <d:resourcetype />
            <d:displayname />
          </d:prop>
        </d:propfind>
        """, auth=auth)
        if r3.status_code != 207:
            return [{"erro": f"Erro ao buscar path do addressbook: {r3.status_code}"}]

        tree = ET.fromstring(r3.text)
        responses = tree.findall('.//d:response', ns)
        addressbook_path = None
        for resp in responses:
            if resp.find('.//d:resourcetype/d:collection', ns) is not None and resp.find('.//d:resourcetype/card:addressbook', {'d': 'DAV:', 'card': 'urn:ietf:params:xml:ns:carddav'}) is not None:
                href = resp.find('d:href', ns)
                if href is not None:
                    addressbook_path = href.text
                    break

        if not addressbook_path:
            return [{"erro": "addressbook não encontrado"}]

        full_url = f"{base_url}{addressbook_path}"

        # Etapa 4: REPORT com dados dos contatos
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
        headers["Depth"] = "1"
        r4 = requests.request("REPORT", full_url, headers=headers, data=report_body, auth=auth)
        if r4.status_code != 207:
            return [{"erro": f"Erro no REPORT: {r4.status_code}", "body": r4.text[:300]}]

        cards = re.findall(r'BEGIN:VCARD.*?END:VCARD', r4.text, re.DOTALL)
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