import os
import re
import vobject
import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree as ET
from unidecode import unidecode
from datetime import datetime

APPLE_ID = os.environ.get("APPLE_ID")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD")
APPLE_CONTACTS_ID = os.environ.get("APPLE_CONTACTS_ID")
CARD_DAV_URL = os.environ.get("CARD_DAV_URL")

HEADERS = {
    "Content-Type": "application/xml; charset=utf-8",
    "Depth": "1"
}

REPORT_BODY = '''<?xml version="1.0" encoding="utf-8" ?>
<card:addressbook-query xmlns:card="urn:ietf:params:xml:ns:carddav">
  <prop xmlns="DAV:">
    <getetag />
    <address-data />
  </prop>
</card:addressbook-query>
'''

def get_contacts_raw():
    try:
        response = requests.request(
            method="REPORT",
            url=CARD_DAV_URL,
            headers=HEADERS,
            data=REPORT_BODY,
            auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD)
        )

        if response.status_code != 207:
            return {"erro": "Erro no REPORT", "status": response.status_code, "request_url": CARD_DAV_URL, "request_headers": HEADERS, "response_headers": dict(response.headers), "body": response.text}

        tree = ET.fromstring(response.content)
        vcards = []
        for response_el in tree.findall(".//{DAV:}response"):
            vcard_data_el = response_el.find(".//{urn:ietf:params:xml:ns:carddav}address-data")
            if vcard_data_el is not None and vcard_data_el.text:
                vcards.append(vcard_data_el.text)

        return vcards

    except Exception as e:
        return {"erro": str(e)}

def parse_vcards(vcards):
    contatos = []
    for vcard_raw in vcards:
        try:
            vcard = vobject.readOne(vcard_raw)
            contato = {}
            contato["nome"] = vcard.fn.value
            contato["nome_normalizado"] = unidecode(contato["nome"]).lower()
            contato["email"] = getattr(vcard, "email", None).value if hasattr(vcard, "email") else None
            contato["telefone"] = getattr(vcard, "tel", None).value if hasattr(vcard, "tel") else None
            contato["empresa"] = getattr(vcard, "org", None).value[0] if hasattr(vcard, "org") else None
            contato["cargo"] = getattr(vcard, "title", None).value if hasattr(vcard, "title") else None

            # Aniversário
            if hasattr(vcard, "bday"):
                bday = vcard.bday.value
                if isinstance(bday, datetime):
                    contato["aniversario"] = bday.date().isoformat()
                elif isinstance(bday, str):
                    try:
                        contato["aniversario"] = datetime.fromisoformat(bday).date().isoformat()
                    except Exception:
                        contato["aniversario"] = bday

            # Endereço
            if hasattr(vcard, "adr"):
                adr = vcard.adr.value
                endereco = ", ".join([str(field) for field in adr if field])
                contato["endereco"] = endereco

            # Notas
            if hasattr(vcard, "note"):
                contato["notas"] = vcard.note.value

            # URLs personalizadas
            contato["linkedin"] = None
            contato["redes"] = []
            if hasattr(vcard, "url"):
                urls = vcard.contents.get("url", [])
                for u in urls:
                    url = u.value
                    if "linkedin.com" in url:
                        contato["linkedin"] = url
                    else:
                        contato["redes"].append(url)

            # Datas extras
            contato["datas"] = []
            for key, content_list in vcard.contents.items():
                if key.startswith("x-") and any("date" in key.lower() for key in u.params.keys() for u in content_list):
                    for item in content_list:
                        data = item.value
                        label = item.params.get("LABEL", [""])[0] if "LABEL" in item.params else ""
                        if isinstance(data, datetime):
                            contato["datas"].append({"label": label, "data": data.date().isoformat()})
                        else:
                            contato["datas"].append({"label": label, "data": str(data)})

            contatos.append(contato)
        except Exception:
            continue

    return contatos

def buscar_por_nome(nome):
    nome_normalizado = unidecode(nome).lower()
    vcards = get_contacts_raw()
    if isinstance(vcards, dict) and "erro" in vcards:
        return vcards

    contatos = parse_vcards(vcards)
    resultado = [c for c in contatos if nome_normalizado in c["nome_normalizado"]]
    return resultado