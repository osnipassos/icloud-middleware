import requests
from requests.auth import HTTPBasicAuth
import os
import xml.etree.ElementTree as ET

def get_contacts():
    url = "https://contacts.icloud.com/"
    auth = HTTPBasicAuth(os.getenv("APPLE_ID"), os.getenv("APPLE_APP_PASSWORD"))

    headers = {
        "Depth": "1",
        "Content-Type": "application/xml"
    }

    body = """
    <d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
        <d:prop>
            <d:displayname />
        </d:prop>
    </d:propfind>
    """

    response = requests.request("PROPFIND", url, headers=headers, data=body, auth=auth)

    if response.status_code != 207:
        raise Exception(f"Erro {response.status_code}: {response.text}")

    tree = ET.fromstring(response.text)
    names = [elem.text for elem in tree.iter() if elem.tag.endswith("displayname")]
    return names