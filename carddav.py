import os
import requests
import vobject
import base64
import re
from unidecode import unidecode

APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.getenv("CARD_DAV_URL")

HEADERS = {
    "Depth": "1",
    "Content-Type": "application/xml; charset=utf-8"
}

def get_auth():
    if not APPLE_ID or not APPLE_APP_PASSWORD:
        return None
    userpass = f"{APPLE_ID}:{APPLE_APP_PASSWORD}"
    token = base64.b64encode(userpass.encode()).decode("utf-8")
    return f"Basic {token}"

def get_contacts_raw():
    if not CARD_DAV_URL:
        return {"erro": "CARD_DAV_URL não configurada"}

    body = """<?xml version='1.0' encoding='utf-8' ?>
    <C:addressbook-query xmlns:D='DAV:' xmlns:C='urn:ietf:params:xml:ns:carddav'>
      <D:prop>
        <D:getetag/>
        <C:address-data/>
      </D:prop>
      <C:filter/>
    </C:addressbook-query>"""

    try:
        response = requests.request(
            "REPORT",
            CARD_DAV_URL,
            headers={**HEADERS, "Authorization": get_auth()},
            data=body
        )
        if response.status_code != 207:
            return {
                "erro": "Erro no REPORT",
                "status": response.status_code,
                "request_url": CARD_DAV_URL,
                "request_headers": HEADERS,
                "response_headers": dict(response.headers),
                "body": response.text
            }

        return parse_vcards(response.text)
    except Exception as e:
        return {"erro": str(e)}

def extract_linkedin(note):
    match = re.search(r"https?://(www\.)?linkedin\.com/in/[\w\-]+", note or "")
    return match.group(0) if match else None

def extract_redes(vcard):
    redes = []
    for attr in vcard.contents.get("x-socialprofile", []):
        redes.append(attr.value)
    return redes or None

def extract_datas(vcard):
    datas = []
    for key, field in vcard.contents.items():
        if key.lower() in ["x-abdate", "x-abevent", "x-abdate1", "x-abdate2"]:
            for entry in field:
                datas.append({
                    "data": str(entry.value),
                    "label": entry.params.get("X-ABLabel", [key])[0]
                })
    return datas or None

def extract_endereco(vcard):
    enderecos = []
    for adr in vcard.contents.get("adr", []):
        endereco = {
            "rua": adr.value.street,
            "cidade": adr.value.city,
            "estado": adr.value.region,
            "cep": adr.value.code,
            "pais": adr.value.country
        }
        enderecos.append(endereco)
    return enderecos or None

def parse_vcards(multistatus_xml):
    vcards = re.findall(r"BEGIN:VCARD.*?END:VCARD", multistatus_xml, re.DOTALL)
    contatos = []

    for vcard_str in vcards:
        try:
            vcard = vobject.readOne(vcard_str)
            nome = getattr(vcard, "fn", None)
            email = getattr(vcard, "email", None)
            telefone = getattr(vcard, "tel", None)
            org = getattr(vcard, "org", None)
            title = getattr(vcard, "title", None)
            note = getattr(vcard, "note", None)
            bday = getattr(vcard, "bday", None)

            contatos.append({
                "nome": nome.value if nome else None,
                "nome_normalizado": unidecode(nome.value.lower()) if nome else None,
                "email": email.value if email else None,
                "telefone": telefone.value if telefone else None,
                "empresa": ";".join(org.value) if org else None,
                "cargo": title.value if title else None,
                "linkedin": extract_linkedin(note.value) if note else None,
                "redes": extract_redes(vcard),
                "datas": extract_datas(vcard),
                "notas": note.value if note else None,
                "aniversario": bday.value if bday else None,
                "enderecos": extract_endereco(vcard)
            })
        except Exception:
            continue

    return {"contatos": contatos}

def find_contacts_by_name(termo):
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "contatos" not in raw:
        return raw

    termo_norm = unidecode(termo.lower())
    resultados = [c for c in raw["contatos"] if termo_norm in (c.get("nome_normalizado") or "")]
    return {"contatos": resultados}