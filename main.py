from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from carddav import get_contacts
import os

app = FastAPI()
API_TOKEN = os.getenv("API_TOKEN", "mellro_super_token_123")

@app.get("/contato")
async def buscar_contato_por_nome(request: Request, nome: str = Query(..., description="Nome parcial ou completo")):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        contatos = get_contacts()
        resultados = [c for c in contatos if nome.lower() in c.get("nome", "").lower()]
        return JSONResponse(content={"contatos": resultados or []})
    except Exception as e:
        return JSONResponse(content={"erro": f"Erro ao buscar contato por nome: {str(e)}"})