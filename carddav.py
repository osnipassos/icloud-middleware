import os
import re
import requests
import vobject
from unidecode import unidecode
from requests.auth import HTTPBasicAuth

def normalize_nome(nome):
    return unidecode(nome.strip().lower())

def get_contacts_raw():
    url = os.getenv("CARD_DAV_URL")
    if not url:
        return {"erro": "CARD_DAV_URL não configurada"}

    auth = HTTPBasicAuth(os.getenv("APPLE_ID"), os.getenv("APPLE_APP_PASSWORD"))
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
  <card:filter/>
</card:addressbook-query>"""

    try:
        response = requests.request("REPORT", url, headers=headers, data=body, auth=auth)
    except Exception as e:
        return {"erro": str(e)}

    if not response.ok:
        return {
            "erro": "Erro no REPORT",
            "status": response.status_code,
            "request_url": url,
            "request_headers": headers,
            "response_headers": dict(response.headers),
            "body": response.text
        }

    return response.text

def parse_vcards(xml_data):
    contatos = []
    vcards = re.findall(r"BEGIN:VCARD.*?END:VCARD", xml_data, re.DOTALL)

    for vcard_text in vcards:
        try:
            vcard = vobject.readOne(vcard_text)
        except Exception:
            continue

        contato = {}
        contato["nome"] = getattr(vcard, "fn", None).value if hasattr(vcard, "fn") else None
        contato["nome_normalizado"] = normalize_nome(contato["nome"]) if contato["nome"] else None

        contato["telefone"] = (
            vcard.tel.value if hasattr(vcard, "tel") else None
        )
        contato["email"] = (
            vcard.email.value if hasattr(vcard, "email") else None
        )
        contato["empresa"] = (
            vcard.org.value[0] if hasattr(vcard, "org") else None
        )
        contato["cargo"] = (
            vcard.title.value if hasattr(vcard, "title") else None
        )
        contato["aniversario"] = (
            str(vcard.bday.value) if hasattr(vcard, "bday") else None
        )
        contato["nota"] = (
            vcard.note.value if hasattr(vcard, "note") else None
        )

        # Endereço formatado
        if hasattr(vcard, "adr"):
            adr = vcard.adr.value
            contato["endereco"] = ", ".join(
                filter(None, [adr.street, adr.city, adr.region, adr.code, adr.country])
            )

        # Datas com label
        datas = []
        for key in vcard.contents:
            if key.lower() == "x-abdate":
                for d in vcard.contents[key]:
                    label = d.params.get("x-ablabel", [""])[0]
                    datas.append({
                        "label": label,
                        "data": str(d.value)
                    })
        contato["datas"] = datas if datas else None

        # LinkedIn e redes sociais
        redes = []
        linkedin = None
        for key in vcard.contents:
            if key.lower() == "x-socialprofile":
                for s in vcard.contents[key]:
                    tipo = s.params.get("type", [""])[0].lower()
                    url = str(s.value)
                    if "linkedin.com" in url or tipo == "linkedin":
                        linkedin = url
                    else:
                        redes.append({"tipo": tipo, "url": url})
        contato["linkedin"] = linkedin
        contato["redes"] = redes if redes else None

        contatos.append(contato)

    return contatos

def buscar_por_nome(contatos, termo):
    termo = normalize_nome(termo)
    resultados = []
    for contato in contatos:
        if not contato["nome_normalizado"]:
            continue
        if all(palavra in contato["nome_normalizado"] for palavra in termo.split()):
            resultados.append(contato)
    return resultados