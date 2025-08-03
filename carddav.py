import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.getenv("CARD_DAV_URL")
APPLE_CONTACTS_ID = os.getenv("APPLE_CONTACTS_ID")

AUTH = (APPLE_ID, APPLE_APP_PASSWORD)

HEADERS = {
    "Content-Type": "application/xml; charset=utf-8",
    "Depth": "1"
}

def get_contacts_raw():
    collection_url = f"{CARD_DAV_URL}/{APPLE_CONTACTS_ID}/carddavhome/card/"

    body = """<?xml version="1.0" encoding="UTF-8"?>
    <A:propfind xmlns:A="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
      <A:prop>
        <A:getetag/>
        <C:address-data/>
      </A:prop>
    </A:propfind>"""

    response = requests.request("REPORT", collection_url, headers=HEADERS, data=body, auth=AUTH)

    if response.status_code != 207:
        raise Exception({
            "erro": "Erro no REPORT",
            "status": response.status_code,
            "request_url": collection_url,
            "request_headers": HEADERS,
            "response_headers": dict(response.headers),
            "body": response.text,
        })

    return response.text