from fastapi import FastAPI, File, UploadFile
import os

app = FastAPI()

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    contents = await file.read()
    
    with open(f"data/{file.filename}", "wb") as f:
        f.write(contents)