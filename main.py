from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome
import os

app = FastAPI()

# Token fixo de autenticação (simples para dev, substitua por algo mais seguro em produção)
TOKEN = "mellro_super_token_123"

@app.middleware("http")
async def check_auth(request: Request, call_next):
    if request.url.path.startswith("/contato") or request.url.path.startswith("/contatos"):
        auth = request.headers.get("Authorization")
        if auth != f"Bearer {TOKEN}":
            return JSONResponse(status_code=401, content={"erro": "Não autorizado"})
    return await call_next(request)

@app.get("/contatos")
def listar_todos():
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return raw
    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
def buscar(nome: str):
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return raw
    contatos = parse_vcards(raw)
    encontrados = buscar_por_nome(nome, contatos)
    return {"contatos": encontrados}