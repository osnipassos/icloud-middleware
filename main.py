from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from carddav import get_contacts_raw, parse_vcards, buscar_por_nome
import os

app = FastAPI()

# CORS liberado total (ajuste se for necessário restringir)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TOKEN = os.getenv("API_TOKEN", "mellro_super_token_123")

def checar_token(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth.split(" ")[1] != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")

@app.get("/contatos")
async def listar_contatos(request: Request):
    checar_token(request)
    try:
        raw = get_contacts_raw()
        contatos = parse_vcards(raw)
        return {"contatos": contatos}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

@app.get("/contato")
async def contato_por_nome(nome: str, request: Request):
    checar_token(request)
    try:
        resultados = buscar_por_nome(nome)
        return {"contatos": resultados}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})