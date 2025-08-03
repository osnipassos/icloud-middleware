from fastapi import FastAPI, Header, Query
from carddav import get_contacts_raw, parse_vcards, find_contacts_by_name  # certifique-se que essa função exista
import os

app = FastAPI()

# Token fixo para autenticação básica
API_TOKEN = "mellro_super_token_123"

@app.get("/contatos")
def contatos(authorization: str = Header(...)):
    if authorization != f"Bearer {API_TOKEN}":
        return {"erro": "Não autorizado"}

    try:
        raw = get_contacts_raw()
        contatos = parse_vcards(raw)
        return {"contatos": contatos}
    except Exception as e:
        return {"erro": str(e)}

@app.get("/contato")
def contato(nome: str = Query(...), authorization: str = Header(...)):
    if authorization != f"Bearer {API_TOKEN}":
        return {"erro": "Não autorizado"}

    try:
        raw = get_contacts_raw()
        contatos = parse_vcards(raw)
        encontrados = find_contacts_by_name(nome, contatos)
        return {"contatos": encontrados}
    except Exception as e:
        return {"erro": str(e)}