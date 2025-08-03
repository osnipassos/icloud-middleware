import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome

app = FastAPI()

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Token de autenticação fake
API_TOKEN = os.getenv("API_TOKEN", "mellro_super_token_123")

def check_auth(request: Request):
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Não autorizado")

@app.get("/contatos")
def listar_contatos(request: Request):
    check_auth(request)
    try:
        vcards = get_contacts_raw()
        contatos = parse_vcards(vcards)
        return {"contatos": contatos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contato")
def buscar_contato(request: Request, nome: str):
    check_auth(request)
    try:
        contatos = buscar_por_nome(nome)
        return {"contatos": contatos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))