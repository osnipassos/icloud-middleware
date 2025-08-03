from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import os
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome

app = FastAPI()
API_TOKEN = os.environ.get("API_TOKEN")

def authorize(token: str):
    return token == f"Bearer {API_TOKEN}"

@app.get("/contatos")
def listar_contatos(authorization: str = Header(None)):
    if not authorize(authorization):
        return JSONResponse(status_code=401, content={"erro": "Não autorizado"})
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return JSONResponse(status_code=500, content=raw)
    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
def buscar_contato(nome: str, authorization: str = Header(None)):
    if not authorize(authorization):
        return JSONResponse(status_code=401, content={"erro": "Não autorizado"})
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return JSONResponse(status_code=500, content=raw)
    contatos = parse_vcards(raw)
    resultados = buscar_por_nome(nome, contatos)
    return {"contatos": resultados}