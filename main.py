from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from carddav import get_contacts
import os

app = FastAPI()
API_TOKEN = os.getenv("API_TOKEN")

@app.get("/contatos")
async def contatos(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or auth_header != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    contatos = get_contacts()
    return JSONResponse(content={"contatos": contatos})