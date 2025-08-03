from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import os
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome

API_TOKEN = os.environ.get("API_TOKEN", "mellro_super_token_123")

app = FastAPI()

def verificar_token(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        return False
    token = authorization.replace("Bearer ", "").strip()
    return token == API_TOKEN

@app.middleware("http")
async def autenticar(request: Request, call_next):
    if request.url.path.startswith("/contato") or request.url.path.startswith("/contatos"):
        auth_header = request.headers.get("Authorization")
        if not verificar_token(auth_header):
            return JSONResponse(status_code=401, content={"erro": "Não autorizado"})
    return await call_next(request)

@app.get("/contatos")
def listar_contatos():
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return raw
    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
def buscar_contato(nome: str = ""):
    if not nome:
        raise HTTPException(status_code=400, detail="Nome é obrigatório")
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return raw
    contatos = parse_vcards(raw)
    resultados = buscar_por_nome(nome, contatos)
    return {"contatos": resultados}