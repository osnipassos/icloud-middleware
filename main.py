import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome

load_dotenv()

app = FastAPI()

origins = [
    "*",  # Ajuste conforme necessário
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_TOKEN = os.getenv("AUTH_TOKEN", "mellro_super_token_123")

def verificar_autenticacao(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token mal formatado")
    token = authorization.replace("Bearer ", "")
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")

@app.get("/contatos")
def listar_contatos(authorization: str = Header(...)):
    verificar_autenticacao(authorization)
    xml = get_contacts_raw()
    if isinstance(xml, dict) and "erro" in xml:
        return xml
    contatos = parse_vcards(xml)
    return {"contatos": contatos}

@app.get("/contato")
def buscar_contato(nome: str, authorization: str = Header(...)):
    verificar_autenticacao(authorization)
    xml = get_contacts_raw()
    if isinstance(xml, dict) and "erro" in xml:
        return xml
    contatos = parse_vcards(xml)
    encontrados = buscar_por_nome(contatos, nome)
    return {"contatos": encontrados}