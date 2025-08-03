import os
import requests
import vobject
from unidecode import unidecode
import re
from requests.auth import HTTPBasicAuth
from datetime import datetime

def normalizar_nome(nome):
    return unidecode(nome).lower().strip()

def buscar_por_nome(nome_busca, contatos):
    nome_busca = normalizar_nome(nome_busca)
    partes_busca = nome_busca.split()

    resultados = []
    for contato in contatos:
        nome_normalizado = contato.get("nome_normalizado", "")
        if all(parte in nome_normalizado for parte in partes_busca):
            resultados.append(contato)
    return resultados

def get_contacts_raw():
    url = os.environ.get("CARD_DAV_URL")
    user = os.environ.get("APPLE_ID")
    password = os.environ.get("APPLE_APP_PASSWORD")

    if not url:
        return {"erro": "CARD_DAV_URL não configurada"}

    try:
        headers = {
            "Content-Type": "application/xml; charset=utf-8",
            "Depth": "1",
        }
        data = """<?xml version="1.0" encoding="utf-8" ?>
        <A:propfind xmlns:A="DAV:">
          <A:prop>
            <A:getetag/>
            <A:address-data xmlns:A="urn:ietf:params:xml:ns:carddav"/>
          </A:prop>
        </A:propfind>"""

        response = requests.request("REPORT", url, headers=headers, data=data, auth=HTTPBasicAuth(user, password))
        if response.status_code != 207:
            return {
                "erro": "Erro no REPORT",
                "status": response.status_code,
                "request_url": url,
                "request_headers": headers,
                "response_headers": dict(response.headers),
                "body": response.text,
            }

        return response.text

    except Exception as e:
        return {"erro": str(e)}

def parse_vcards(response_text):
    if isinstance(response_text, dict) and "erro" in response_text:
        return response_text

    contatos = []
    pattern = r'BEGIN:VCARD(.*?)END:VCARD'
    matches = re.findall(pattern, response_text, re.DOTALL)

    for match in matches:
        vcard_str = f"BEGIN:VCARD{match}END:VCARD"
        try:
            vcard = vobject.readOne(vcard_str)

            contato = {}
            contato["nome"] = str(vcard.fn.value) if hasattr(vcard, "fn") else None
            contato["nome_normalizado"] = normalizar_nome(contato["nome"]) if contato["nome"] else ""

            contato["email"] = str(vcard.email.value) if hasattr(vcard, "email") else None
            contato["telefone"] = str(vcard.tel.value) if hasattr(vcard, "tel") else None
            contato["empresa"] = str(vcard.org.value[0]) if hasattr(vcard, "org") and vcard.org.value else None
            contato["cargo"] = str(vcard.title.value) if hasattr(vcard, "title") else None

            # Notas
            contato["notas"] = str(vcard.note.value) if hasattr(vcard, "note") else None

            # Endereço
            if hasattr(vcard, "adr"):
                endereco = vcard.adr.value
                endereco_str = ", ".join(filter(None, [
                    endereco.street,
                    endereco.city,
                    endereco.region,
                    endereco.code,
                    endereco.country
                ]))
                contato["endereco"] = endereco_str.strip()
            else:
                contato["endereco"] = None

            # Aniversário
            if hasattr(vcard, "bday"):
                bday = vcard.bday.value
                if isinstance(bday, datetime):
                    contato["aniversario"] = bday.date().isoformat()
                else:
                    contato["aniversario"] = str(bday)

            # Redes sociais e URLs
            contato["linkedin"] = None
            contato["redes"] = []
            if hasattr(vcard, "url_list"):
                for url_obj in vcard.url_list:
                    url = url_obj.value
                    tipo = url_obj.params.get("TYPE", [""])[0].lower() if hasattr(url_obj, "params") else ""
                    if "linkedin" in url.lower():
                        contato["linkedin"] = url
                    else:
                        contato["redes"].append({"tipo": tipo, "url": url})
            elif hasattr(vcard, "url"):
                url = vcard.url.value
                if "linkedin" in url.lower():
                    contato["linkedin"] = url
                else:
                    contato["redes"].append({"tipo": "", "url": url})

            # Datas
            contato["datas"] = []
            if hasattr(vcard, "x_abdate"):
                for x in vcard.contents.get("x_abdate", []):
                    valor = x.value
                    label = x.params.get("X-ABLABEL", [""])[0] if "X-ABLABEL" in x.params else ""
                    contato["datas"].append({"label": label, "data": valor})

            contatos.append(contato)

        except Exception as e:
            contatos.append({"erro": "Erro ao processar vcard", "detalhe": str(e)})

    return contatos