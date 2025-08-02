from fastapi import FastAPI, Query, Request, HTTPException
from carddav import get_contacts_raw, parse_vcards

app = FastAPI()

API_TOKEN = "mellro_super_token_123"

@app.get("/contato")
def buscar_contato_por_nome(request: Request, nome: str = Query(..., description="Nome parcial ou completo")):
    token = request.headers.get("Authorization")
    if token != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        raw = get_contacts_raw()
        contatos = parse_vcards(raw)
        resultados = [c for c in contatos if nome.lower() in c.get("nome", "").lower()]
        return {"contatos": resultados or ["Nenhum contato encontrado"]}
    except Exception as e:
        return {"erro": f"Erro ao buscar contato por nome: {str(e)}"}