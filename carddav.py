import os
import requests
import vobject
import re
from unidecode import unidecode
from base64 import b64encode

def get_contacts_raw():
    url = os.environ.get("CARD_DAV_URL")
    if not url:
        return {"erro": "CARD_DAV_URL não configurada"}

    auth = (os.environ.get("APPLE_ID"), os.environ.get("APPLE_APP_PASSWORD"))
    if not all(auth):
        return {"erro": "Credenciais não configuradas"}

    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
    }

    body = """<?xml version="1.0" encoding="UTF-8"?>
    <A:propfind xmlns:A="DAV:">
      <A:prop>
        <A:getetag/>
      </A:prop>
    </A:propfind>"""

    resp = requests.request("REPORT", url, headers=headers, data=body, auth=auth)
    if resp.status_code != 207:
        return {
            "erro": "Erro no REPORT",
            "status": resp.status_code,
            "request_url": url,
            "request_headers": headers,
            "response_headers": dict(resp.headers),
            "body": resp.text
        }

    vcards = []
    for href in re.findall(r"<D:href>(.*?)</D:href>", resp.text):
        if not href.endswith(".vcf"):
            continue
        card_url = f"https://contacts.icloud.com{href}"
        card_resp = requests.get(card_url, auth=auth)
        if card_resp.ok:
            vcards.append(card_resp.text)

    return vcards


def parse_vcards(vcards):
    contatos = []
    for vcard_str in vcards:
        try:
            vcard = vobject.readOne(vcard_str)
            contato = {}

            if hasattr(vcard, 'fn'):
                contato['nome'] = vcard.fn.value
                contato['nome_normalizado'] = unidecode(vcard.fn.value.lower())

            if hasattr(vcard, 'email'):
                contato['email'] = vcard.email.value

            if hasattr(vcard, 'tel'):
                contato['telefone'] = vcard.tel.value

            if hasattr(vcard, 'org'):
                contato['empresa'] = ";".join(vcard.org.value)

            if hasattr(vcard, 'title'):
                contato['cargo'] = vcard.title.value

            if hasattr(vcard, 'bday'):
                contato['aniversario'] = str(vcard.bday.value)

            if hasattr(vcard, 'note'):
                contato['notas'] = vcard.note.value

            if hasattr(vcard, 'adr'):
                contato['endereco'] = " ".join(vcard.adr.value)

            # Redes sociais e datas customizadas
            contato['linkedin'] = None
            contato['redes'] = None
            contato['datas'] = []

            if hasattr(vcard, 'x_socialprofile'):
                contato['redes'] = vcard.x_socialprofile.value

            for attr in vcard.contents.get('x-abdate', []):
                data_val = attr.value.isoformat() if hasattr(attr.value, 'isoformat') else str(attr.value)
                contato['datas'].append({"data": data_val, "label": attr.params.get("X-ABLABEL", [""])[0]})

            contatos.append(contato)
        except Exception as e:
            continue
    return contatos


def find_contacts_by_name(nome_busca, contatos):
    nome_busca_normalizado = unidecode(nome_busca.strip().lower())

    encontrados = []
    for contato in contatos:
        campos = [
            contato.get("nome", ""),
            contato.get("email", ""),
            contato.get("telefone", ""),
            contato.get("empresa", ""),
            contato.get("cargo", "")
        ]
        texto = " ".join(campos)
        texto_normalizado = unidecode(texto.lower())

        if nome_busca_normalizado in texto_normalizado:
            encontrados.append(contato)

    return encontrados