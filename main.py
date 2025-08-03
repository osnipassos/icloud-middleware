import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TOKEN = os.getenv("API_TOKEN", "mellro_super_token_123")

def autenticar(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou inválido")
    token = authorization.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")

@app.get("/")
def read_root():
    return {"mensagem": "Middleware de Contatos iCloud ativo."}

@app.get("/contatos")
def listar_contatos(request: Request):
    autenticar(request.headers.get("Authorization"))
    raw = get_contacts_raw()
    contatos = parse_vcards(raw)
    if isinstance(contatos, dict) and "erro" in contatos:
        return contatos
    return {"contatos": contatos}

@app.get("/contato")
def buscar_contato(nome: str, request: Request):
    autenticar(request.headers.get("Authorization"))
    raw = get_contacts_raw()
    contatos = parse_vcards(raw)
    if isinstance(contatos, dict) and "erro" in contatos:
        return contatos
    resultado = buscar_por_nome(nome, contatos)
    return {"contatos": resultado}