from fastapi import FastAPI, File, UploadFile
import os

app = FastAPI()

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    contents = await file.read()
    os.makedirs("data", exist_ok=True)  # Garante que a pasta existe
    with open(f"data/{file.filename}", "wb") as f:
        f.write(contents)
    return {"message": f"Arquivo {file.filename} salvo com sucesso"}
