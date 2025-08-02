import requests
from requests.auth import HTTPBasicAuth
import os
import xml.etree.ElementTree as ET

def get_contacts():
    auth = HTTPBasicAuth(os.getenv("APPLE_ID"), os.getenv("APPLE_APP_PASSWORD"))
    headers = {
        "Depth": "0",
        "Content-Type": "application/xml"
    }

    discovery_body = """
    <d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
        <d:prop>
            <d:current-user-principal />
        </d:prop>
    </d:propfind>
    """

    # Fase 1 – Descobrir a URL do usuário
    discovery_url = "https://contacts.icloud.com/"
    discovery_response = requests.request("PROPFIND", discovery_url, headers=headers, data=discovery_body, auth=auth)

    print("DISCOVERY STATUS:", discovery_response.status_code)
    print("DISCOVERY BODY:", discovery_response.text[:1000])

    if discovery_response.status_code != 207:
        return [f"Erro de discovery {discovery_response.status_code}: {discovery_response.text}"]

    tree = ET.fromstring(discovery_response.text)
    ns = {'d': 'DAV:'}
    principal_url = tree.find('.//d:current-user-principal/d:href', ns)
    if principal_url is None:
        return ["Erro: não foi possível encontrar o href do usuário"]

    user_path = principal_url.text
    addressbook_url = f"https://contacts.icloud.com{user_path}/"

    # Fase 2 – Buscar os nomes
    body = """
    <d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
        <d:prop>
            <d:displayname />
        </d:prop>
    </d:propfind>
    """
    headers["Depth"] = "1"
    response = requests.request("PROPFIND", addressbook_url, headers=headers, data=body, auth=auth)

    print("CARDDAV STATUS:", response.status_code)
    print("CARDDAV BODY:", response.text[:1000])

    if response.status_code != 207:
        return [f"Erro {response.status_code}: {response.text}"]

    tree = ET.fromstring(response.text)
    names = [elem.text for elem in tree.iter() if elem.tag.endswith("displayname")]
    return names or ["Nenhum contato encontrado"]