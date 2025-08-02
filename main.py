from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from carddav import get_contacts_raw, parse_vcards, find_contacts_by_name
import os

app = FastAPI()

API_TOKEN = os.getenv("API_TOKEN", "mellro_super_token_123")

def verificar_autenticacao(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticação ausente")

    token = auth_header.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")

@app.get("/contatos")
async def listar_contatos(request: Request):
    verificar_autenticacao(request)
    contatos = parse_vcards(get_contacts_raw())
    return JSONResponse(content={"contatos": contatos}, ensure_ascii=False)

@app.get("/contato")
async def buscar_contato(request: Request, nome: str):
    verificar_autenticacao(request)
    contatos_filtrados = find_contacts_by_name(nome)
    return JSONResponse(content={"contatos": contatos_filtrados}, ensure_ascii=False)