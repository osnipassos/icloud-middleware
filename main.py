import os
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from carddav import get_contacts_raw, parse_vcards, normalizar_nome

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
app = FastAPI()


def validar_token(token: str):
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")


@app.get("/contatos")
def listar_contatos(authorization: str = Header(None)):
    validar_token(authorization.replace("Bearer ", ""))
    try:
        raw = get_contacts_raw()
        contatos = parse_vcards(raw)
        return {"contatos": contatos}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})


@app.get("/contato")
def buscar_contato(nome: str, authorization: str = Header(None)):
    validar_token(authorization.replace("Bearer ", ""))
    try:
        raw = get_contacts_raw()
        todos = parse_vcards(raw)
        termo = normalizar_nome(nome)
        filtrados = [c for c in todos if termo in c.get("nome_normalizado", "")]
        return {"contatos": filtrados}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})