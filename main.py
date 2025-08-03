from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome
import os

app = FastAPI()

# CORS liberado geral
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TOKEN = os.environ.get("API_TOKEN", "mellro_super_token_123")

def verificar_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou inválido")
    token = auth.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")

@app.get("/contatos")
async def listar_contatos(request: Request):
    verificar_token(request)
    raw = get_contacts_raw()
    if isinstance(raw, dict) and "erro" in raw:
        return {"erro": str(raw)}
    contatos = parse_vcards(raw)
    return {"contatos": contatos}

@app.get("/contato")
async def buscar_contato(nome: str, request: Request):
    verificar_token(request)
    contatos = buscar_por_nome(nome)
    if isinstance(contatos, dict) and "erro" in contatos:
        return {"erro": str(contatos)}
    return {"contatos": contatos}