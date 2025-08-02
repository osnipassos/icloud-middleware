import os
import requests
import base64
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from unidecode import unidecode

def get_contacts_raw():
    apple_id = os.getenv("APPLE_ID")
    app_password = os.getenv("APPLE_APP_PASSWORD")
    carddav_url = os.getenv("CARD_DAV_URL")

    if not carddav_url:
        return {"erro": "CARD_DAV_URL não configurada"}

    auth_string = f"{apple_id}:{app_password}"
    encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
        "Authorization": f"Basic {encoded_auth}"
    }

    body = """<?xml version="1.0" encoding="utf-8" ?>
    <C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
      <D:prop>
        <D:getetag/>
        <C:address-data/>
      </D:prop>
      <C:filter>
        <C:prop-filter name="FN"/>
      </C:filter>
    </C:addressbook-query>
    """

    try:
        response = requests.request("REPORT", carddav_url, headers=headers, data=body)
        if response.status_code != 207:
            return {
                "erro": "Erro no REPORT",
                "status": response.status_code,
                "request_url": carddav_url,
                "request_headers": headers,
                "response_headers": dict(response.headers),
                "body": response.text
            }

        return response.text
    except Exception as e:
        return {"erro": "Exceção no REPORT", "detalhes": str(e)}

def parse_vcards(multistatus_xml):
    contatos = []
    try:
        root = ET.fromstring(multistatus_xml)
        for response in root.findall("{DAV:}response"):
            card = response.find(".//{urn:ietf:params:xml:ns:carddav}address-data")
            if card is not None and card.text:
                contato = extrair_dados_vcard(card.text)
                if contato:
                    contatos.append(contato)
    except ET.ParseError:
        pass
    return contatos

def extrair_dados_vcard(vcard_text):
    contato = {}
    redes = {}
    datas = []

    lines = vcard_text.splitlines()
    for line in lines:
        line = line.strip()

        if line.startswith("FN:"):
            contato["nome"] = line.replace("FN:", "").strip()
            contato["nome_normalizado"] = unidecode(contato["nome"].lower())
        elif line.startswith("ORG:"):
            contato["empresa"] = line.replace("ORG:", "").strip()
        elif line.startswith("TITLE:"):
            contato["cargo"] = line.replace("TITLE:", "").strip()
        elif line.startswith("EMAIL"):
            partes = line.split(":")
            if len(partes) == 2:
                contato["email"] = partes[1].strip()
        elif line.startswith("TEL"):
            partes = line.split(":")
            if len(partes) == 2:
                contato["telefone"] = partes[1].strip()
        elif line.startswith("URL"):
            partes = line.split(":")
            if len(partes) == 2:
                url = partes[1].strip()
                if "linkedin.com" in url:
                    contato["linkedin"] = url
                elif "facebook.com" in url:
                    redes["facebook"] = url
                elif "skype.com" in url:
                    redes["skype"] = url
        elif line.startswith("X-ABDATE") or line.startswith("X-APPLE-DATE"):
            match_data = re.search(r":(\d{4}-\d{2}-\d{2})", line)
            match_label = re.search(r"LABEL=([^;:]+)", line)
            if match_data and match_label:
                datas.append({
                    "data": match_data.group(1),
                    "label": match_label.group(1)
                })

    if redes:
        contato["redes"] = redes
    if datas:
        contato["datas"] = datas

    return contato if "nome" in contato else None

def buscar_por_nome(termo_nome):
    multistatus_xml = get_contacts_raw()
    if isinstance(multistatus_xml, dict) and "erro" in multistatus_xml:
        return multistatus_xml

    contatos = parse_vcards(multistatus_xml)

    termo = unidecode(termo_nome.strip().lower())

    filtrados = []
    for c in contatos:
        if termo in c.get("nome_normalizado", ""):
            filtrados.append({
                "nome": c.get("nome"),
                "email": c.get("email"),
                "telefone": c.get("telefone"),
                "empresa": c.get("empresa"),
                "cargo": c.get("cargo"),
                "linkedin": c.get("linkedin"),
                "redes": c.get("redes"),
                "datas": c.get("datas")
            })

    return {"contatos": filtrados}