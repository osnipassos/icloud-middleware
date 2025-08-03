import os
import requests
import vobject
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

CARD_DAV_URL = os.getenv("CARD_DAV_URL")
APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
APPLE_CONTACTS_ID = os.getenv("APPLE_CONTACTS_ID")

AUTH = (APPLE_ID, APPLE_APP_PASSWORD)
HEADERS = {"Content-Type": "application/xml; charset=utf-8", "Depth": "1"}


def get_contacts_raw():
    collection_url = f"{CARD_DAV_URL}/{APPLE_CONTACTS_ID}/"  # Corrigido

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


def parse_vcards(xml_data):
    soup = BeautifulSoup(xml_data, "xml")
    vcards = soup.find_all("address-data")
    contatos = []

    for vcard in vcards:
        try:
            vcard_parsed = vobject.readOne(vcard.text)
            contato = {}

            if hasattr(vcard_parsed, "fn"):
                contato["nome"] = vcard_parsed.fn.value
                contato["nome_normalizado"] = vcard_parsed.fn.value.lower()

            if hasattr(vcard_parsed, "email"):
                contato["email"] = vcard_parsed.email.value

            if hasattr(vcard_parsed, "tel"):
                contato["telefone"] = vcard_parsed.tel.value

            if hasattr(vcard_parsed, "adr"):
                endereco = vcard_parsed.adr.value
                contato["endereco"] = " ".join(filter(None, [
                    endereco.street, endereco.city, endereco.region, endereco.code, endereco.country
                ])).strip()

            if hasattr(vcard_parsed, "title"):
                contato["cargo"] = vcard_parsed.title.value

            if hasattr(vcard_parsed, "org"):
                contato["empresa"] = " ".join(vcard_parsed.org.value)

            if hasattr(vcard_parsed, "bday"):
                contato["aniversario"] = str(vcard_parsed.bday.value)

            if hasattr(vcard_parsed, "url"):
                contato["linkedin"] = vcard_parsed.url.value

            datas = []
            for prop in vcard_parsed.getChildren():
                if prop.name.lower().startswith("x-abdate") or prop.name.lower().startswith("x-abrelateddate"):
                    datas.append({
                        "label": prop.group if prop.group else "",
                        "data": prop.value
                    })
            if datas:
                contato["datas"] = datas

            contatos.append(contato)
        except Exception:
            continue

    return contatos


def buscar_por_nome(nome_busca):
    xml = get_contacts_raw()
    contatos = parse_vcards(xml)
    nome_busca = nome_busca.lower()
    return [
        c for c in contatos
        if nome_busca in c.get("nome_normalizado", "")
    ]