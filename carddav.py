import os
import vobject
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

APPLE_ID = os.environ.get("APPLE_ID")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.environ.get("CARD_DAV_URL")

def get_contacts_raw():
    url = CARD_DAV_URL
    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1"
    }

    data = """<?xml version="1.0" encoding="UTF-8"?>
    <A:propfind xmlns:A="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
        <A:prop>
            <A:getetag />
            <C:address-data />
        </A:prop>
    </A:propfind>"""

    response = requests.request(
        "REPORT",
        url,
        headers=headers,
        data=data,
        auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD)
    )

    if response.status_code != 207:
        raise Exception(("Erro no REPORT", response.status_code, url, response.headers, response.text))

    soup = BeautifulSoup(response.content, "xml")
    vcards = []
    for address_data in soup.find_all("address-data"):
        try:
            vcard = vobject.readOne(address_data.text)
            vcards.append(vcard)
        except Exception:
            continue

    return vcards

def parse_vcards(vcards):
    contatos = []
    for vcard in vcards:
        contato = {
            "nome_completo": None,
            "apelido": None,
            "telefones": [],
            "emails": [],
            "endereco": None,
            "empresa": None,
            "cargo": None,
            "notas": None,
            "aniversario": None,
            "linkedin": None,
        }

        for key in vcard.contents.keys():
            if key == "fn":
                contato["nome_completo"] = str(vcard.contents[key][0].value)
            elif key == "nickname":
                contato["apelido"] = str(vcard.contents[key][0].value)
            elif key == "tel":
                contato["telefones"].append(str(vcard.contents[key][0].value))
            elif key == "email":
                contato["emails"].append(str(vcard.contents[key][0].value))
            elif key == "adr":
                endereco_obj = vcard.contents[key][0].value
                endereco_str = ", ".join(filter(None, [
                    endereco_obj.street,
                    endereco_obj.city,
                    endereco_obj.region,
                    endereco_obj.code,
                    endereco_obj.country
                ]))
                contato["endereco"] = endereco_str if endereco_str else None
            elif key == "org":
                org = vcard.contents[key][0].value
                if isinstance(org, list) and len(org) > 0:
                    contato["empresa"] = org[0]
            elif key == "title":
                contato["cargo"] = str(vcard.contents[key][0].value)
            elif key == "note":
                contato["notas"] = str(vcard.contents[key][0].value)
            elif key == "bday":
                contato["aniversario"] = str(vcard.contents[key][0].value)
            elif "x-socialprofile" in key:
                value = vcard.contents[key][0].value
                if "linkedin" in value.lower():
                    if not value.startswith("http"):
                        value = value.replace("x-", "").strip().replace(":", "")
                        contato["linkedin"] = f"https://www.linkedin.com/in/{value}"
                    else:
                        contato["linkedin"] = value

        contatos.append(contato)

    return contatos

def buscar_por_nome(vcards, nome_busca):
    nome_busca = nome_busca.lower()
    encontrados = []

    for vcard in vcards:
        nome = vcard.fn.value.lower() if hasattr(vcard, 'fn') else ''
        apelido = getattr(vcard, 'nickname', None)
        apelido = apelido.value.lower() if apelido else ''

        if nome_busca in nome or nome_busca in apelido:
            encontrados.append(vcard)

    return encontrados