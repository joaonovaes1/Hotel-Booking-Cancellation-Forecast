from fastapi import FastAPI, File, UploadFile
import os
import pandas as pd
from minio import Minio
from sqlalchemy import create_engine
from fastapi import HTTPException
import requests
import time

from dotenv import load_dotenv
load_dotenv() 

app = FastAPI()


TB_URL = "http://localhost:8081"
TB_USERNAME = "tenant@thingsboard.org"
TB_PASSWORD = "tenant"

def get_tb_jwt_token() -> str:
    url = f"{TB_URL}/api/auth/login"
    payload = {
        "username": TB_USERNAME,
        "password": TB_PASSWORD,
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["token"]


@app.get("/")
def root():
    return {"message": "API rodando!"}



@app.post("/load-from-minio-to-neondb/")
async def load_from_minio_to_neondb():
    try:
        
        minio_client = Minio(
            endpoint="localhost:9000",
            access_key="admin",
            secret_key="admin123",
            secure=False,
        )

        bucket_name = "hotel-booking-data"
        object_name = "hotel_booking_demand.csv"
        local_file_path = "/tmp/hotel_booking_demand.csv"

        minio_client.fget_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=local_file_path,
        )

        df = pd.read_csv(local_file_path)

        database_url = os.getenv("NEON_DATABASE_URL")
        if database_url is None:
            raise Exception("NEON_DATABASE_URL is not set!")
        engine = create_engine(database_url)

        df.to_sql("hotel_bookings", engine, if_exists="replace", index=False)

        return {"message": "Dados carregados com sucesso no NeonDB"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


DEVICE_ACCESS_TOKEN = "kJ9J52P5fkoZ9O0hcLNO"  

DEVICE_ID = "69ec8b40-cfb7-11f0-9110-1fd13077b503"  # device de validação

@app.post("/thingsboard-to-minio/")
async def thingsboard_to_minio():
    try:
        # 0) obter token JWT
        jwt_token = get_tb_jwt_token()
        print("Token TB:", jwt_token[:20], "...")

        # 1) buscar telemetria do device de VALIDAÇÃO
        DEVICE_ID = "69ec8b40-cfb7-11f0-9110-1fd13077b503"
        url_ts = f"{TB_URL}/api/plugins/telemetry/DEVICE/{DEVICE_ID}/values/timeseries"
        
        keys_list = [
            "hotel", "is_canceled", "lead_time", "arrival_date_year", "arrival_date_month",
            "arrival_date_week_number", "arrival_date_day_of_month", "adults", "children",
            "babies", "meal", "country", "market_segment", "distribution_channel",
            "is_repeated_guest", "previous_cancellations", "previous_bookings_not_canceled",
            "reserved_room_type", "assigned_room_type", "booking_changes", "deposit_type",
            "agent", "company", "days_in_waiting_list", "customer_type", "adr",
            "required_car_parking_spaces", "total_of_special_requests", "reservation_status",
            "reservation_status_date"
        ]
        params = {
            "keys": ",".join(keys_list),
            "startTs": "0",
            "endTs": str(int(time.time() * 1000)),
            "limit": "200000"
        }
        headers = {"X-Authorization": f"Bearer {jwt_token}"}

        resp = requests.get(url_ts, params=params, headers=headers)
        print("Status telemetria:", resp.status_code)
        print("Resposta raw:", resp.text[:500])
        resp.raise_for_status()
        ts_data = resp.json()
        print(f"Telemetria recebida: {len(ts_data)} chaves")

        # 2) converter timeseries para DataFrame - ROBUSTO
        rows = []
        if ts_data:
            # Encontra uma chave com dados
            ref_key = None
            for k in ts_data:
                if ts_data[k]:
                    ref_key = k
                    break
            
            if ref_key:
                n_records = len(ts_data[ref_key])
                print(f"Número de registros: {n_records}")

                for i in range(n_records):
                    row = {"ts": ts_data[ref_key][i]["ts"]}
                    for k, series in ts_data.items():
                        if i < len(series):
                            row[k] = series[i]["value"]
                        else:
                            row[k] = None
                    rows.append(row)
            else:
                print("Nenhuma chave com dados")

        df = pd.DataFrame(rows)
        print(f"DataFrame criado com {len(df)} linhas")

        # 3) salvar CSV e enviar MinIO
        local_csv_path = "/tmp/hotel_booking_demand_validation.csv"
        df.to_csv(local_csv_path, index=False)

        minio_client = Minio(
            endpoint="localhost:9000",
            access_key="admin",
            secret_key="admin123",
            secure=False,
        )

        bucket_name = "hotel-booking-data"
        object_name = "hotel_booking_demand_validation.csv"

        if not minio_client.bucket_exists(bucket_name=bucket_name):
            minio_client.make_bucket(bucket_name=bucket_name)

        minio_client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=local_csv_path,
        )

        return {
            "message": "Dados de validação enviados da ThingsBoard para o MinIO",
            "linhas": len(df),
            "chaves": len(ts_data) if ts_data else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
@app.post("/load-validation-to-neondb/")
async def load_validation_to_neondb():
    try:
        minio_client = Minio(
            endpoint="localhost:9000",
            access_key="admin",
            secret_key="admin123",
            secure=False,
        )

        bucket_name = "hotel-booking-data"
        object_name = "hotel_booking_demand_validation.csv"  # ← SÓ validação
        local_file_path = "/tmp/hotel_booking_demand_validation.csv"

        minio_client.fget_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=local_file_path,
        )

        df = pd.read_csv(local_file_path)
        print(f"CSV baixado com {len(df)} linhas")

        database_url = os.getenv("NEON_DATABASE_URL")
        if database_url is None:
            raise Exception("NEON_DATABASE_URL is not set!")
        engine = create_engine(database_url)

        # Salva em tabela específica para validação
        df.to_sql("hotel_bookings_validation", engine, if_exists="replace", index=False)

        return {"message": "Dados de VALIDAÇÃO carregados no NeonDB", "linhas": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/csv-full-to-minio/")
async def csv_full_to_minio():
    try:
        # 1) localizar o CSV original
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.normpath(os.path.join(base_dir, "..", "data", "hotel_bookings.csv"))

        if not os.path.exists(csv_path):
            raise Exception(f"Arquivo CSV não encontrado em: {csv_path}")

        df = pd.read_csv(csv_path)
        print(f"CSV original carregado com {len(df)} linhas")

        # 2) salvar CSV temporário (se quiser pode usar o próprio csv_path)
        local_csv_path = "/tmp/hotel_booking_demand_full.csv"
        df.to_csv(local_csv_path, index=False)

        # 3) enviar para MinIO
        minio_client = Minio(
            endpoint="localhost:9000",
            access_key="admin",
            secret_key="admin123",
            secure=False,
        )

        bucket_name = "hotel-booking-data"
        object_name = "hotel_booking_demand_full.csv"

        if not minio_client.bucket_exists(bucket_name=bucket_name):
            minio_client.make_bucket(bucket_name=bucket_name)

        minio_client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=local_csv_path,
        )

        return {
            "message": "CSV COMPLETO enviado para o MinIO com sucesso",
            "linhas": len(df),
            "bucket": bucket_name,
            "objeto": object_name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@app.post("/load-full-to-neondb/")
async def load_full_to_neondb():
    try:
        # 1) conecta no MinIO
        minio_client = Minio(
            endpoint="localhost:9000",
            access_key="admin",
            secret_key="admin123",
            secure=False,
        )

        bucket_name = "hotel-booking-data"
        object_name = "hotel_booking_demand_full.csv"
        local_file_path = "/tmp/hotel_booking_demand_full.csv"

        # 2) baixa o CSV completo do MinIO
        minio_client.fget_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=local_file_path,
        )

        df = pd.read_csv(local_file_path)
        print(f"CSV FULL baixado com {len(df)} linhas")

        # 3) conecta no NeonDB
        database_url = os.getenv("NEON_DATABASE_URL")
        if database_url is None:
            raise Exception("NEON_DATABASE_URL is not set!")
        engine = create_engine(database_url)

        # 4) grava na tabela principal (sobrescreve)
        df.to_sql("hotel_bookings", engine, if_exists="replace", index=False)

        return {
            "message": "DADOS COMPLETOS carregados no NeonDB na tabela hotel_bookings",
            "linhas": len(df),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



