from fastapi import FastAPI, Header, HTTPException, Query
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome
import os

app = FastAPI()

API_TOKEN = os.getenv("API_TOKEN", "mellro_super_token_123")


def validar_token(authorization: str = Header(...)):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Token inválido")


@app.get("/contatos")
def listar_contatos(authorization: str = Header(...)):
    validar_token(authorization)
    try:
        xml = get_contacts_raw()
        contatos = parse_vcards(xml)
        return {"contatos": contatos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contato")
def contato_por_nome(nome: str = Query(...), authorization: str = Header(...)):
    validar_token(authorization)
    try:
        contatos = buscar_por_nome(nome)
        return {"contatos": contatos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))