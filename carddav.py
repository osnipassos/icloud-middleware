import os
import re
import requests
import vobject
from unidecode import unidecode
from datetime import date, datetime

ICLOUD_URL = os.getenv("CARD_DAV_URL")
ICLOUD_USER = os.getenv("CARD_DAV_USER")
ICLOUD_PASS = os.getenv("CARD_DAV_PASS")

def get_contacts_raw():
    if not ICLOUD_URL:
        return {"erro": "CARD_DAV_URL não configurada"}

    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1"
    }

    body = """<?xml version="1.0" encoding="UTF-8"?>
    <C:calendar-query xmlns:C="urn:ietf:params:xml:ns:caldav">
        <D:prop xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
            <D:getetag />
            <C:calendar-data />
        </D:prop>
    </C:calendar-query>"""

    try:
        response = requests.request(
            "REPORT",
            ICLOUD_URL,
            headers=headers,
            data=body,
            auth=(ICLOUD_USER, ICLOUD_PASS)
        )
        if response.status_code != 207:
            return {
                "erro": "Erro no REPORT",
                "status": response.status_code,
                "request_url": ICLOUD_URL,
                "request_headers": headers,
                "response_headers": dict(response.headers),
                "body": response.text
            }
        return response.text
    except Exception as e:
        return {"erro": str(e)}

def parse_vcards(raw_xml):
    if not isinstance(raw_xml, str):
        return []

    vcards = re.findall("BEGIN:VCARD(.*?)END:VCARD", raw_xml, re.DOTALL)
    contatos = []
    for v in vcards:
        try:
            vcard = vobject.readOne("BEGIN:VCARD" + v + "END:VCARD")
            contato = {}

            if hasattr(vcard, "fn"):
                contato["nome"] = vcard.fn.value
                contato["nome_normalizado"] = normalize_name(vcard.fn.value)
            if hasattr(vcard, "email"):
                contato["email"] = vcard.email.value
            if hasattr(vcard, "tel"):
                contato["telefone"] = vcard.tel.value
            if hasattr(vcard, "org"):
                contato["empresa"] = " ".join(vcard.org.value)
            if hasattr(vcard, "title"):
                contato["cargo"] = vcard.title.value
            if hasattr(vcard, "note"):
                contato["nota"] = vcard.note.value
            if hasattr(vcard, "url"):
                url = vcard.url.value
                if "linkedin.com" in url:
                    contato["linkedin"] = url
                else:
                    contato["redes"] = url
            if hasattr(vcard, "bday") and hasattr(vcard.bday, "value"):
                bday_val = vcard.bday.value
                if isinstance(bday_val, (date, datetime)):
                    contato["aniversario"] = bday_val.isoformat()
                elif isinstance(bday_val, str):
                    contato["aniversario"] = bday_val
            if hasattr(vcard, "adr"):
                endereco = vcard.adr.value
                contato["endereco"] = ", ".join(
                    filter(None, [endereco.street, endereco.city, endereco.region, endereco.code, endereco.country])
                )

            # eventos extras
            if hasattr(vcard, "x_apple_relatednames"):
                contato["relacionados"] = vcard.x_apple_relatednames.value

            # datas extras
            datas = []
            for c in vcard.contents.get("x-abdate", []):
                valor = c.value
                label = c.params.get("x-ablabel", [""])[0]
                datas.append({"label": label, "data": valor})
            if datas:
                contato["datas"] = datas

            contatos.append(contato)
        except Exception:
            continue

    return contatos

def normalize_name(nome):
    return unidecode(nome.strip().lower())

def buscar_por_nome(contatos, nome_busca):
    nome_busca = normalize_name(nome_busca)
    partes = nome_busca.split()

    resultado = []
    for contato in contatos:
        nome_norm = contato.get("nome_normalizado", "")
        if all(p in nome_norm for p in partes):
            resultado.append(contato)

    return resultado