from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from carddav import get_contacts_raw, parse_vcards, find_contacts_by_name
import os

app = FastAPI()

def check_auth(request: Request):
    token = request.headers.get("Authorization", "")
    if token != "Bearer mellro_super_token_123":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/contatos")
async def listar_contatos(request: Request):
    check_auth(request)
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return raw
    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
async def buscar_contato(nome: str, request: Request):
    check_auth(request)
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return raw
    contatos = parse_vcards(raw)
    encontrados = find_contacts_by_name(nome, contatos)
    return {"contatos": encontrados}