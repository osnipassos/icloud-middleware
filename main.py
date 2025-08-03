from fastapi import FastAPI, Request, Header
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome
import os

app = FastAPI()

API_TOKEN = os.getenv("API_TOKEN", "mellro_super_token_123")

def authorize(auth: str = Header(...)):
    if auth != f"Bearer {API_TOKEN}":
        raise Exception("Não autorizado")

@app.get("/contatos")
def listar_contatos(request: Request, authorization: str = Header(...)):
    try:
        authorize(authorization)
        raw = get_contacts_raw()
        contatos = parse_vcards(raw)
        return {"contatos": contatos}
    except Exception as e:
        return {"erro": str(e)}

@app.get("/contato")
def buscar_contato(nome: str, authorization: str = Header(...)):
    try:
        authorize(authorization)
        contatos = buscar_por_nome(nome)
        return {"contatos": contatos}
    except Exception as e:
        return {"erro": str(e)}