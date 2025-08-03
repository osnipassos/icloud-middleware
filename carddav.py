import os
import base64
import requests
import xml.etree.ElementTree as ET
import vobject
from unidecode import unidecode

def get_contacts_raw():
    url = os.getenv("CARD_DAV_URL")
    if not url:
        return {"erro": "CARD_DAV_URL não configurada"}

    auth = base64.b64encode(f"{os.getenv('APPLE_ID')}:{os.getenv('APPLE_APP_PASSWORD')}".encode()).decode()
    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
        "Authorization": f"Basic {auth}",
    }
    data = """<?xml version="1.0" encoding="UTF-8"?>
    <C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
        <D:prop>
            <D:getetag/>
            <C:address-data/>
        </D:prop>
    </C:addressbook-query>"""

    response = requests.request("REPORT", url, headers=headers, data=data)

    if not response.ok:
        return {
            "erro": "Erro no REPORT",
            "status": response.status_code,
            "request_url": url,
            "request_headers": {k: v for k, v in headers.items() if k != "Authorization"},
            "response_headers": dict(response.headers),
            "body": response.text
        }

    root = ET.fromstring(response.content)
    vcards = []
    for response_elem in root.findall(".//{DAV:}response"):
        address_data = response_elem.find(".//{urn:ietf:params:xml:ns:carddav}address-data")
        if address_data is not None and address_data.text:
            vcards.append(address_data.text)

    return vcards

def parse_vcards(vcards):
    contatos = []

    for vcard_str in vcards:
        try:
            vcard = vobject.readOne(vcard_str)
        except Exception:
            continue

        contato = {}

        if hasattr(vcard, "fn"):
            contato["nome"] = vcard.fn.value
            contato["nome_normalizado"] = normalizar_nome(vcard.fn.value)

        if hasattr(vcard, "email"):
            contato["email"] = vcard.email.value

        if hasattr(vcard, "tel"):
            contato["telefone"] = vcard.tel.value

        if hasattr(vcard, "org"):
            contato["empresa"] = vcard.org.value[0] if vcard.org.value else None

        if hasattr(vcard, "title"):
            contato["cargo"] = vcard.title.value

        if hasattr(vcard, "bday"):
            contato["aniversario"] = vcard.bday.value.isoformat()

        if hasattr(vcard, "note"):
            contato["notas"] = vcard.note.value

        if hasattr(vcard, "adr"):
            endereco = vcard.adr.value
            endereco_formatado = " ".join(filter(None, [
                endereco.street,
                endereco.city,
                endereco.region,
                endereco.code,
                endereco.country
            ]))
            contato["endereco"] = endereco_formatado.strip()

        # Redes sociais e campos extras
        contato["linkedin"] = None
        contato["redes"] = []
        contato["datas"] = []

        for attr in vcard.getChildren():
            if attr.name == "url" and "linkedin.com" in attr.value:
                contato["linkedin"] = attr.value
            elif attr.name == "url":
                contato["redes"].append(attr.value)
            elif attr.name == "x-abdate":
                data = attr.value
                label = attr.params.get("x-ablabel", [""])[0]
                contato["datas"].append({
                    "label": label,
                    "data": data.isoformat() if hasattr(data, "isoformat") else str(data)
                })

        contatos.append(contato)

    return contatos

def buscar_por_nome(contatos, termo_busca):
    termo_normalizado = normalizar_nome(termo_busca)
    resultados = []
    for contato in contatos:
        nome_normalizado = contato.get("nome_normalizado", "")
        if all(parte in nome_normalizado for parte in termo_normalizado.split()):
            resultados.append(contato)
    return resultados

def normalizar_nome(nome):
    return unidecode(nome).lower().replace(";", "").strip()