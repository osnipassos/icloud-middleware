from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from carddav import get_contacts_raw, parse_vcards

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TOKEN = os.getenv("API_TOKEN")

@app.middleware("http")
async def check_auth(request: Request, call_next):
    if request.url.path.startswith("/contato") or request.url.path == "/contatos":
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"erro": "Token ausente"})
        token = auth_header.split("Bearer ")[-1]
        if token != API_TOKEN:
            return JSONResponse(status_code=403, content={"erro": "Token inválido"})
    return await call_next(request)

@app.get("/contatos")
def contatos():
    resultado = get_contacts_raw()
    if "vcard" in resultado:
        return {"contatos": parse_vcards(resultado["vcard"])}
    else:
        return {"contatos": [resultado]}

@app.get("/contato")
def contato_por_nome(nome: str):
    try:
        resultado = get_contacts_raw()
        if "vcard" not in resultado:
            return {"contatos": [resultado]}

        contatos = parse_vcards(resultado["vcard"])
        filtrados = [c for c in contatos if nome.lower() in (c["nome_completo"] or "").lower()]
        return {"contatos": filtrados}
    except Exception as e:
        return {"erro": f"Erro ao buscar contato por nome: {str(e)}"}