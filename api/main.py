from fastapi import FastAPI, File, UploadFile
import os
import pandas as pd
from minio import Minio
from sqlalchemy import create_engine
from fastapi import HTTPException

from dotenv import load_dotenv
load_dotenv() 

app = FastAPI()


@app.get("/")
def root():
    return {"message": "API rodando!"}


@app.post("/load-from-minio-to-neondb/")
async def load_from_minio_to_neondb():
    try:
        minio_client = Minio(
            endpoint="localhost:9010",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
            )
        
        bucket_name = "hotel-booking-data"
        object_name = "hotel_booking_demand.csv"
        local_file_path = "/tmp/hotel_booking_demand.csv"
        
    
        minio_client.fget_object(bucket_name=bucket_name,
                                object_name=object_name, file_path=local_file_path)

        df = pd.read_csv(local_file_path)

        database_url = os.getenv("NEON_DATABASE_URL")
        if database_url is None:
            raise Exception("NEON_DATABASE_URL is not set!")
        engine = create_engine(database_url)
    
        # Salva no NeonDB (em uma tabela chamada hotel_bookings)
        df.to_sql("hotel_bookings", engine, if_exists="replace", index=False)

        return {"message": "Dados carregados com sucesso no NeonDB"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))