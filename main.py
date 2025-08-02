from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from carddav import get_contacts_raw, parse_vcards, normalize
import os

API_TOKEN = os.environ.get("API_TOKEN")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def auth(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer ") or token.split(" ")[1] != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/contatos")
async def listar_contatos(request: Request):
    auth(request)
    raw = get_contacts_raw()
    if "vcard" in raw:
        contatos = parse_vcards(raw["vcard"])
        return JSONResponse(content={"contatos": contatos})
    return JSONResponse(content={"contatos": [raw]})


@app.get("/contato")
async def buscar_contato(request: Request, nome: str):
    auth(request)
    try:
        raw = get_contacts_raw()
        if "vcard" in raw:
            contatos = parse_vcards(raw["vcard"])
            nome_normalizado = normalize(nome)
            filtrados = [c for c in contatos if nome_normalizado in c.get("nome_normalizado", "")]
            return JSONResponse(content={"contatos": filtrados})
        else:
            return JSONResponse(content={"erro": "Erro ao buscar contato por nome", **raw})
    except Exception as e:
        return JSONResponse(content={"erro": f"Exceção inesperada: {str(e)}"})