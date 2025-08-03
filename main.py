import os
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome

app = FastAPI()

TOKEN_ESPERADO = os.getenv("AUTH_TOKEN", "mellro_super_token_123")

@app.get("/contatos")
def listar_contatos(authorization: str = Header(None)):
    if authorization != f"Bearer {TOKEN_ESPERADO}":
        return JSONResponse(content={"erro": "Não autorizado"}, status_code=401)

    raw = get_contacts_raw()
    if isinstance(raw, dict) and raw.get("erro"):
        return JSONResponse(content=raw, status_code=400)

    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
def buscar_contato(nome: str, authorization: str = Header(None)):
    if authorization != f"Bearer {TOKEN_ESPERADO}":
        return JSONResponse(content={"erro": "Não autorizado"}, status_code=401)

    raw = get_contacts_raw()
    if isinstance(raw, dict) and raw.get("erro"):
        return JSONResponse(content=raw, status_code=400)

    contatos = parse_vcards(raw)
    resultado = buscar_por_nome(contatos, nome)
    return {"contatos": resultado}