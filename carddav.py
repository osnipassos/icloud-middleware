import os
import requests
import vobject
from requests.auth import HTTPBasicAuth
from unidecode import unidecode

CARD_DAV_URL = os.getenv("CARD_DAV_URL")
APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")


def get_contacts_raw():
    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
    }

    data = """<?xml version="1.0" encoding="UTF-8"?>
    <A:addressbook-query xmlns:A="DAV:" xmlns:B="urn:ietf:params:xml:ns:carddav">
        <A:prop>
            <A:getetag/>
            <B:address-data/>
        </A:prop>
        <B:filter/>
    </A:addressbook-query>"""

    response = requests.request(
        "REPORT",
        CARD_DAV_URL,
        headers=headers,
        data=data,
        auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD),
    )

    if response.status_code != 207:
        raise Exception(
            {
                "erro": "Erro no REPORT",
                "status": response.status_code,
                "request_url": CARD_DAV_URL,
                "request_headers": headers,
                "response_headers": dict(response.headers),
                "body": response.text,
            }
        )

    return response.text


def parse_vcards(response_text):
    contatos = []
    for vcard_str in response_text.split("END:VCARD"):
        if "BEGIN:VCARD" not in vcard_str:
            continue
        try:
            vcard = vobject.readOne(vcard_str + "END:VCARD\n")
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

            if hasattr(vcard, "url"):
                url = vcard.url.value
                if "linkedin" in url:
                    contato["linkedin"] = url
                else:
                    contato["site"] = url

            datas = []
            for attr in vcard.contents.get("x-abdate", []):
                data_item = {
                    "label": attr.params.get("X-ABLabel", [""])[0],
                    "data": attr.value,
                }
                datas.append(data_item)
            if datas:
                contato["datas"] = datas

            contatos.append(contato)
        except Exception as e:
            print("Erro ao processar vcard:", e)
            continue
    return contatos


def normalizar_nome(nome):
    return unidecode(nome.strip().lower())