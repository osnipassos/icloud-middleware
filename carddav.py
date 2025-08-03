import os
import re
from urllib.parse import unquote
from vobject import readOne
from caldav import DAVClient as CardDAVClient  # ✅ Corrigido

APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.getenv("CARD_DAV_URL")

def normalizar_nome(nome):
    if not nome:
        return ""
    nome = nome.lower()
    nome = re.sub(r"[^a-zA-Z0-9\s]", "", nome)
    return nome.strip()

def conectar_carddav():
    if not (APPLE_ID and APPLE_APP_PASSWORD and CARD_DAV_URL):
        raise Exception("Variáveis de ambiente não configuradas corretamente")
    return CardDAVClient(
        url=CARD_DAV_URL,
        username=APPLE_ID,
        password=APPLE_APP_PASSWORD
    )

def get_contacts_raw():
    try:
        client = conectar_carddav()
        principal = client.principal()
        addressbooks = principal.addressbooks()
        all_vcards = []
        for book in addressbooks:
            vcards = book.cards()
            all_vcards.extend(vcards)
        return all_vcards
    except Exception as e:
        return {"erro": str(e)}

def parse_vcards(raw_vcards):
    contatos = []
    for vcard in raw_vcards:
        try:
            v = readOne(vcard.vcard)
            contato = {}
            contato["nome"] = str(v.fn.value) if hasattr(v, "fn") else None
            contato["nome_normalizado"] = normalizar_nome(contato["nome"])
            contato["email"] = str(v.email.value) if hasattr(v, "email") else None
            contato["telefone"] = str(v.tel.value) if hasattr(v, "tel") else None
            contato["empresa"] = str(v.org.value[0]) if hasattr(v, "org") else None
            contato["cargo"] = str(v.title.value) if hasattr(v, "title") else None
            contato["aniversario"] = v.bday.value.isoformat() if hasattr(v, "bday") and hasattr(v.bday.value, "isoformat") else str(v.bday.value) if hasattr(v, "bday") else None
            contato["endereco"] = str(v.adr.value) if hasattr(v, "adr") else None
            contato["linkedin"] = str(v.linkedin.value) if hasattr(v, "linkedin") else None
            contato["notas"] = str(v.note.value) if hasattr(v, "note") else None

            datas = []
            for attr in v.getChildren():
                if attr.name == "X-APPLE-DATE":
                    datas.append({
                        "label": attr.params.get("X-APPLE-LABEL", [""])[0],
                        "data": str(attr.value)
                    })
            contato["datas"] = datas if datas else None

            contatos.append(contato)
        except Exception as e:
            continue
    return contatos

def buscar_por_nome(nome_busca):
    vcards = get_contacts_raw()
    if isinstance(vcards, dict) and "erro" in vcards:
        return vcards
    contatos = parse_vcards(vcards)
    nome_normalizado = normalizar_nome(nome_busca)
    return [c for c in contatos if nome_normalizado in c["nome_normalizado"]]