import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
PORT = int(os.getenv("PORT", 8000))

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/contatos")
def listar_contatos(request: Request):
    autenticar(request)
    raw, erro = get_contacts_raw()
    if erro:
        return erro
    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
def buscar_contato(nome: str, request: Request):
    autenticar(request)
    raw, erro = get_contacts_raw()
    if erro:
        return erro
    contatos = parse_vcards(raw)
    resultados = buscar_por_nome(nome, contatos)
    return {"contatos": resultados}

def autenticar(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")
    token = auth.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")