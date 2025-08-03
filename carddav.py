import os
import re
from urllib.parse import unquote
from vobject import readOne
from carddav import CardDAVClient

CARD_DAV_URL = os.getenv("CARD_DAV_URL")
APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
APPLE_CONTACTS_ID = os.getenv("APPLE_CONTACTS_ID")
CARD_DAV_HOME = f"{CARD_DAV_URL}/{APPLE_CONTACTS_ID}/card/"

def normalizar_nome(nome):
    return re.sub(r'[^a-zA-Z0-9]', ' ', nome).strip().lower()

def get_contacts_raw():
    client = CardDAVClient(CARD_DAV_URL)
    client.set_basic_auth(APPLE_ID, APPLE_APP_PASSWORD)
    try:
        return client.find_resources(url=CARD_DAV_HOME)
    except Exception as e:
        raise Exception({
            "erro": "Erro no REPORT",
            "status": 400,
            "request_url": CARD_DAV_HOME,
            "request_headers": {
                "Content-Type": "application/xml; charset=utf-8",
                "Depth": "1"
            },
            "response_headers": getattr(e, 'response_headers', {}),
            "body": str(e)
        })

def parse_vcards(resources):
    contatos = []
    for res in resources:
        try:
            vcard = readOne(res.data.decode())
            contato = {
                "nome": getattr(vcard, 'fn', None).value if hasattr(vcard, 'fn') else None,
                "nome_normalizado": normalizar_nome(getattr(vcard, 'fn', None).value if hasattr(vcard, 'fn') else ""),
                "email": getattr(vcard, 'email', None).value if hasattr(vcard, 'email') else None,
                "telefone": getattr(vcard, 'tel', None).value if hasattr(vcard, 'tel') else None,
                "empresa": getattr(vcard, 'org', None).value[0] if hasattr(vcard, 'org') else None,
                "cargo": getattr(vcard, 'title', None).value if hasattr(vcard, 'title') else None,
                "aniversario": (
                    vcard.bday.value.isoformat()
                    if hasattr(vcard, 'bday') and hasattr(vcard.bday.value, 'isoformat')
                    else vcard.bday.value if hasattr(vcard, 'bday') else None
                ),
                "endereco": (
                    " ".join([part for part in vcard.adr.value if part])
                    if hasattr(vcard, 'adr') and hasattr(vcard.adr, 'value') else None
                ),
                "linkedin": next((u.value for u in getattr(vcard, 'url', []) if "linkedin" in u.value.lower()), None)
                    if hasattr(vcard, 'url') else None,
                "datas": []
            }

            if hasattr(vcard, 'x-abdate'):
                if isinstance(vcard.contents.get('x-abdate', []), list):
                    for data_item in vcard.contents.get('x-abdate', []):
                        label = data_item.params.get('X-ABLabel', [''])[0] if data_item.params else ''
                        contato["datas"].append({
                            "label": label,
                            "data": data_item.value
                        })
            contatos.append(contato)
        except Exception as e:
            continue
    return contatos

def buscar_por_nome(nome):
    recursos = get_contacts_raw()
    contatos = parse_vcards(recursos)
    nome = normalizar_nome(nome)
    return [c for c in contatos if nome in c["nome_normalizado"]]