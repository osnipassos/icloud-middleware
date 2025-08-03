import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from carddav import get_contacts_raw, buscar_por_nome, parse_vcards

API_TOKEN = os.environ.get("API_TOKEN")

app = FastAPI()

# Middleware CORS (opcional, mas útil se for integrar com front-end)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def autenticar(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Não autorizado")

@app.get("/contato")
def buscar_contato(nome: str, request: Request):
    autenticar(request)
    try:
        raw = get_contacts_raw()
        contatos = buscar_por_nome(raw, nome)
        return {"contatos": contatos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contatos")
def listar_todos_contatos(request: Request):
    autenticar(request)
    try:
        raw = get_contacts_raw()
        contatos = parse_vcards(raw)
        return {"contatos": contatos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))