from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from carddav import get_contacts_raw, buscar_por_nome
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
app = FastAPI()

# CORS liberado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Autenticação por header
def autenticar(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")

@app.get("/contatos")
def listar_contatos(authorization: str = Header(None)):
    autenticar(authorization)
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return {"erro": raw}
    contatos = buscar_por_nome("")  # traz todos
    return {"contatos": contatos}

@app.get("/contato")
def buscar_contato(nome: str, authorization: str = Header(None)):
    autenticar(authorization)
    contatos = buscar_por_nome(nome)
    return {"contatos": contatos}