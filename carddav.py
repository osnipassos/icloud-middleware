import os
import requests
import vobject
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.getenv("CARD_DAV_URL")

HEADERS = {
    "Depth": "1",
    "Content-Type": "application/xml; charset=utf-8"
}

XML_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:prop>
    <d:getetag/>
    <card:address-data/>
  </d:prop>
</card:addressbook-query>"""

def get_contacts_raw():
    auth = (APPLE_ID, APPLE_APP_PASSWORD)
    try:
        response = requests.request(
            "REPORT",
            CARD_DAV_URL,
            headers=HEADERS,
            data=XML_BODY,
            auth=auth
        )
        if response.status_code != 207:
            raise Exception((
                "Erro no REPORT",
                response.status_code,
                CARD_DAV_URL,
                dict(response.headers),
                response.text,
            ))

        soup = BeautifulSoup(response.content, "xml")
        vcards = [vcard.text for vcard in soup.find_all("address-data")]
        return vcards
    except Exception as e:
        raise Exception(f"Erro ao obter contatos: {e}")

def parse_vcards(vcards):
    contatos = []
    for vcard_str in vcards:
        try:
            vcard = vobject.readOne(vcard_str)
            contato = {}

            # Nome e apelido
            contato["nome_completo"] = getattr(vcard, "fn", None).value if hasattr(vcard, "fn") else None
            contato["apelido"] = getattr(vcard, "nickname", None).value if hasattr(vcard, "nickname") else None

            # Telefones
            contato["telefones"] = []
            if hasattr(vcard, "tel_list"):
                for tel in vcard.tel_list:
                    contato["telefones"].append(tel.value)

            # Emails
            contato["emails"] = []
            if hasattr(vcard, "email_list"):
                for email in vcard.email_list:
                    contato["emails"].append(email.value)

            # Endereços
            if hasattr(vcard, "adr"):
                contato["endereco"] = " ".join([s for s in vcard.adr.value if s])
            else:
                contato["endereco"] = None

            # Organização e cargo
            contato["empresa"] = getattr(vcard, "org", None).value[0] if hasattr(vcard, "org") else None
            contato["cargo"] = getattr(vcard, "title", None).value if hasattr(vcard, "title") else None

            # Notas
            contato["notas"] = getattr(vcard, "note", None).value if hasattr(vcard, "note") else None

            # Aniversário
            contato["aniversario"] = getattr(vcard, "bday", None).value if hasattr(vcard, "bday") else None

            # Redes sociais (com foco em LinkedIn)
            contato["linkedin"] = None
            if hasattr(vcard, "url_list"):
                for url in vcard.url_list:
                    link = url.value.strip()
                    if "linkedin" in link:
                        if not link.startswith("http"):
                            link = f"https://www.linkedin.com/in/{link}"
                        contato["linkedin"] = link
                        break

            contatos.append(contato)
        except Exception as e:
            print(f"Erro ao processar vCard: {e}")
    return contatos

def buscar_por_nome(nome_busca):
    vcards = get_contacts_raw()
    contatos = parse_vcards(vcards)
    nome_busca_normalizado = nome_busca.lower()
    return [
        c for c in contatos
        if c["nome_completo"] and nome_busca_normalizado in c["nome_completo"].lower()
        or (c.get("apelido") and nome_busca_normalizado in c["apelido"].lower())
    ]