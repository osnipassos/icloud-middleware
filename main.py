from fastapi import FastAPI
from dotenv import load_dotenv
from carddav import get_contacts

load_dotenv()

app = FastAPI()

@app.get("/contatos")
def contatos():
    contatos = get_contacts()
    return {"contatos": contatos}