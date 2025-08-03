import os
import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from vobject import readOne
from datetime import datetime

APPLE_ID = os.environ.get("APPLE_ID")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD")
CARD_DAV_URL = os.environ.get("CARD_DAV_URL")  # deve terminar com "/"

HEADERS = {
    "Content-Type": "application/xml; charset=utf-8",
    "Depth": "1"
}

def get_contacts_raw():
    body = """<?xml version="1.0" encoding="utf-8" ?>
    <A:propfind xmlns:A="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
        <A:prop>
            <A:getetag />
            <C:address-data />
        </A:prop>
    </A:propfind>"""

    try:
        res = requests.request(
            method="REPORT",
            url=CARD_DAV_URL,  # garantir que termina com /
            headers=HEADERS,
            auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD),
            data=body
        )
        if res.status_code != 207:
            raise Exception("Erro no REPORT", res.status_code, res.url, res.headers, res.text)

        soup = BeautifulSoup(res.text, "xml")
        vcards = soup.find_all("address-data")
        return [vcard.text for vcard in vcards]

    except Exception as e:
        return {"erro": str(e)}

def parse_vcards(vcards):
    contatos = []

    for vcard_str in vcards:
        try:
            vcard = readOne(vcard_str)
            nome = getattr(vcard, 'fn', None).value if hasattr(vcard, 'fn') else None
            apelido = getattr(vcard, 'nickname', None).value if hasattr(vcard, 'nickname') else None
            email = getattr(vcard, 'email', None).value if hasattr(vcard, 'email') else None
            telefone = None
            if hasattr(vcard, 'tel'):
                telefone = vcard.tel.value
            endereco = None
            if hasattr(vcard, 'adr'):
                adr = vcard.adr.value
                endereco = " ".join(filter(None, [adr.street, adr.city, adr.region, adr.code, adr.country]))
            aniversario = None
            if hasattr(vcard, 'bday'):
                try:
                    aniversario = vcard.bday.value.isoformat()
                except:
                    aniversario = str(vcard.bday.value)
            empresa = vcard.org.value[0] if hasattr(vcard, 'org') else None
            cargo = getattr(vcard, 'title', None).value if hasattr(vcard, 'title') else None
            notas = getattr(vcard, 'note', None).value if hasattr(vcard, 'note') else None
            urls = [vcard.url.value] if hasattr(vcard, 'url') else []

            datas = []
            if hasattr(vcard, 'x-abdate'):
                datas.append({"label": "", "data": vcard.x_abdate.value})

            contatos.append({
                "nome": nome,
                "nome_normalizado": normalizar(nome),
                "apelido": apelido,
                "email": email,
                "telefone": telefone,
                "endereco": endereco,
                "aniversario": aniversario,
                "empresa": empresa,
                "cargo": cargo,
                "notas": notas,
                "linkedin": next((u for u in urls if "linkedin.com" in u), None),
                "datas": datas
            })

        except Exception as e:
            continue

    return contatos

def normalizar(texto):
    if not texto:
        return ""
    return texto.strip().lower()

def buscar_por_nome(nome):
    nome_proc = normalizar(nome)
    vcards = get_contacts_raw()
    if isinstance(vcards, dict) and "erro" in vcards:
        return vcards
    contatos = parse_vcards(vcards)
    resultados = [c for c in contatos if nome_proc in c["nome_normalizado"]]
    return resultados