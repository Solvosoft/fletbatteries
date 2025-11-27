from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# Permitir CORS desde tu frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringir a ["http://localhost:8000"]
    allow_methods=["*"],
    allow_headers=["*"]
)

class ContentPayload(BaseModel):
    title: str
    content: str

# Guardar contenido
@app.post("/save")
async def save_content(payload: ContentPayload):
    print("Contenido recibido:", payload.dict())
    return JSONResponse({"status": "ok", "message": "Contenido guardado con éxito"})

# Cargar contenido
@app.get("/load/{form_id}")
async def load_content(form_id: int):
    contenido = f"<p>Texto inicial para editor {form_id} desde backend</p>"
    return JSONResponse({"status": "ok", "content": contenido})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)