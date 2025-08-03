from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from carddav import get_contacts_raw, buscar_por_nome, parse_vcards
import os

API_TOKEN = os.getenv("API_TOKEN")
app = FastAPI()

def verificar_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou inválido")
    token = authorization.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")

@app.get("/contatos")
def listar_contatos(authorization: str = Header(None)):
    verificar_token(authorization)
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return JSONResponse(content={"erro": raw}, status_code=500)
    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
def buscar_contato(nome: str, authorization: str = Header(None)):
    verificar_token(authorization)
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return JSONResponse(content={"erro": raw}, status_code=500)
    contatos = buscar_por_nome(raw, nome)
    return {"contatos": contatos}