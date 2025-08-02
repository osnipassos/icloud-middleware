from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome
import os

app = FastAPI()

API_TOKEN = os.getenv("API_TOKEN", "mellro_super_token_123")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if "authorization" not in request.headers:
        raise HTTPException(status_code=401, detail="Token não fornecido")

    auth = request.headers["authorization"]
    if auth != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=403, detail="Token inválido")

    return await call_next(request)

@app.get("/contatos")
def contatos():
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return JSONResponse(content={"contatos": [raw]})
    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
def contato(nome: str):
    resultado = buscar_por_nome(nome)
    return resultado