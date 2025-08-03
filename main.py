from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome
import os

app = FastAPI()

API_TOKEN = os.getenv("API_TOKEN", "mellro_super_token_123")

def validar_token(token: str):
    return token == f"Bearer {API_TOKEN}"

@app.get("/contatos")
def listar_contatos(authorization: str = Header(None)):
    if not validar_token(authorization):
        return JSONResponse(status_code=401, content={"erro": "Não autorizado"})

    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return raw

    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
def buscar_contato(nome: str, authorization: str = Header(None)):
    if not validar_token(authorization):
        return JSONResponse(status_code=401, content={"erro": "Não autorizado"})

    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return raw

    contatos = parse_vcards(raw)
    resultados = buscar_por_nome(contatos, nome)

    return {"contatos": resultados}