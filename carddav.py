import os
import requests
import vobject
from unidecode import unidecode

CARD_DAV_URL = os.environ.get("CARD_DAV_URL")
APPLE_ID = os.environ.get("APPLE_ID")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD")

def normalizar_nome(nome):
    return unidecode(nome.lower())

def get_contacts_raw():
    auth = (APPLE_ID, APPLE_APP_PASSWORD)
    headers = {
        "Depth": "1",
        "Content-Type": "application/xml; charset=utf-8",
    }
    body = """<?xml version="1.0" encoding="UTF-8"?>
<card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:prop>
    <d:getetag/>
    <card:address-data/>
  </d:prop>
</card:addressbook-query>
"""
    response = requests.request(
        "REPORT",
        CARD_DAV_URL,
        headers=headers,
        auth=auth,
        data=body,
    )
    if not response.ok:
        raise Exception({
            "erro": "Erro no REPORT",
            "status": response.status_code,
            "request_url": CARD_DAV_URL,
            "request_headers": headers,
            "response_headers": dict(response.headers),
            "body": response.text,
        })
    return response.text

def parse_vcards(response_text):
    contatos = []
    for vcard in vobject.readComponents(response_text):
        contato = {}

        if hasattr(vcard, "fn"):
            contato["nome"] = vcard.fn.value
            contato["nome_normalizado"] = normalizar_nome(vcard.fn.value)

        if hasattr(vcard, "email"):
            contato["email"] = vcard.email.value

        if hasattr(vcard, "tel"):
            contato["telefone"] = vcard.tel.value

        if hasattr(vcard, "org"):
            contato["empresa"] = " ".join(vcard.org.value)

        if hasattr(vcard, "title"):
            contato["cargo"] = vcard.title.value

        if hasattr(vcard, "bday"):
            try:
                contato["aniversario"] = vcard.bday.value.isoformat()
            except:
                contato["aniversario"] = str(vcard.bday.value)

        if hasattr(vcard, "note"):
            contato["notas"] = vcard.note.value

        if hasattr(vcard, "adr"):
            try:
                contato["endereco"] = " ".join(
                    [x for x in vcard.adr.value.__dict__.values() if x]
                )
            except:
                pass

        # Extra: redes sociais (como linkedin), datas e urls extras
        if hasattr(vcard, "url"):
            url = vcard.url.value
            if "linkedin" in url:
                contato["linkedin"] = url
            else:
                contato["site"] = url

        datas = []
        for attr in vcard.contents.get("x-abdate", []):
            data_item = {"label": attr.params.get("X-ABLabel", [""])[0], "data": attr.value}
            datas.append(data_item)
        if datas:
            contato["datas"] = datas

        contatos.append(contato)
    return contatos

def buscar_por_nome(nome_busca):
    nome_busca_normalizado = normalizar_nome(nome_busca)
    raw = get_contacts_raw()
    contatos = parse_vcards(raw)
    return [c for c in contatos if nome_busca_normalizado in c.get("nome_normalizado", "")]