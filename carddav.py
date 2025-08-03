import os
import re
import requests
import vobject
from requests.auth import HTTPBasicAuth
from unidecode import unidecode
from dotenv import load_dotenv

load_dotenv()

APPLE_ID = os.getenv("APPLE_ID")
APPLE_APP_PASSWORD = os.getenv("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.getenv("CARD_DAV_URL")

def normalizar_nome(nome):
    return unidecode(nome).lower()

def get_contacts_raw():
    if not CARD_DAV_URL:
        return None, {"erro": "CARD_DAV_URL não configurada"}

    headers = {
        "Content-Type": "application/xml; charset=utf-8",
        "Depth": "1",
    }

    body = """
    <A:propfind xmlns:A="DAV:">
      <A:prop>
        <A:getetag />
        <A:address-data xmlns:A="urn:ietf:params:xml:ns:carddav" />
      </A:prop>
    </A:propfind>
    """

    response = requests.request(
        "REPORT",
        CARD_DAV_URL,
        headers=headers,
        data=body,
        auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD)
    )

    if not response.ok:
        return None, {
            "erro": "Erro no REPORT",
            "status": response.status_code,
            "request_url": CARD_DAV_URL,
            "request_headers": headers,
            "response_headers": dict(response.headers),
            "body": response.text
        }

    return response.text, None

def parse_vcards(xml_response):
    vcards_raw = re.findall(r"BEGIN:VCARD.*?END:VCARD", xml_response, re.DOTALL)
    contatos = []

    for vcard_text in vcards_raw:
        try:
            vcard = vobject.readOne(vcard_text)
        except Exception:
            continue

        contato = {}
        contato["nome"] = getattr(vcard, "fn", type("obj", (), {"value": None}))().value
        contato["nome_normalizado"] = normalizar_nome(contato["nome"]) if contato["nome"] else None

        contato["email"] = getattr(vcard, "email", type("obj", (), {"value": None}))().value
        contato["telefone"] = getattr(vcard, "tel", type("obj", (), {"value": None}))().value

        contato["empresa"] = getattr(vcard, "org", type("obj", (), {"value": None}))().value
        if isinstance(contato["empresa"], list):
            contato["empresa"] = " ".join(contato["empresa"])

        contato["cargo"] = getattr(vcard, "title", type("obj", (), {"value": None}))().value

        # aniversário
        bday = getattr(vcard, "bday", None)
        if bday:
            contato["aniversario"] = bday.value.isoformat() if hasattr(bday.value, "isoformat") else str(bday.value)

        # endereço
        endereco = getattr(vcard, "adr", None)
        if endereco:
            parts = [
                endereco.value.street,
                endereco.value.city,
                endereco.value.region,
                endereco.value.code,
                endereco.value.country
            ]
            contato["endereco"] = " ".join(filter(None, parts)).replace("  ", " ")

        # datas (X-APPLE-DATE or similar)
        datas = []
        for attr in dir(vcard):
            if attr.startswith("x_") and "date" in attr:
                item = getattr(vcard, attr)
                if hasattr(item, "value"):
                    datas.append({"label": "", "data": str(item.value)})
        contato["datas"] = datas if datas else None

        # redes sociais (X-SOCIALPROFILE)
        redes = []
        linkedin = None
        for line in vcard.contents.get("x-socialprofile", []):
            valor = str(line.value)
            tipo = line.params.get("type", [""])[0].lower()
            if "linkedin" in valor.lower() or tipo == "linkedin":
                linkedin = valor
            else:
                redes.append({"tipo": tipo, "url": valor})
        contato["linkedin"] = linkedin
        contato["redes"] = redes if redes else None

        contatos.append(contato)

    return contatos

def buscar_por_nome(nome, contatos):
    nome_busca = normalizar_nome(nome)
    resultados = []
    for contato in contatos:
        nome_completo = contato.get("nome_normalizado", "")
        if nome_busca in nome_completo:
            resultados.append(contato)
        else:
            # busca por pedaços do nome
            partes = nome_completo.split()
            if any(nome_busca in parte for parte in partes):
                resultados.append(contato)
    return resultados