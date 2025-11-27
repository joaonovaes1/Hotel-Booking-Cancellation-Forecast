import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Pega a string de conexão do NeonDB da variável de ambiente
database_url = os.getenv("NEON_DATABASE_URL")

# Cria o engine para conexão
engine = create_engine(database_url)

# Consulta os primeiros registros da tabela hotel_bookings
query = "SELECT * FROM hotel_bookings LIMIT 10;"

# Executa a consulta e armazena em um DataFrame pandas
df = pd.read_sql(query, engine)

print(df)
