import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hotel Booking Cancellation", layout="wide")

# Sidebar de navegação
st.sidebar.title("Navegação")
page = st.sidebar.radio(
    "Ir para",
    ["Visão geral", "Dados & IoT", "Modelos & MLflow", "Simular reserva"],
)

st.title("Hotel Booking Cancellation – IoT + ML Pipeline")

if page == "Visão geral":
    st.subheader("Panorama do projeto")
    st.write(
        "Pipeline de cancelamento de reservas: CSV → ThingsBoard (IoT) → MinIO → NeonDB → "
        "notebooks/MLflow → Streamlit."
    )

elif page == "Dados & IoT":
    st.subheader("📊 Dados em tempo real (Validação)")
    
    # Conecta NeonDB
    load_dotenv()
    database_url = os.getenv("NEON_DATABASE_URL")
    engine = create_engine(database_url)
    
    # Métrica total
    st.metric("Total registros validação", 18021)
    
    # Tabela das últimas linhas (manter)
    recent_data = pd.read_sql("SELECT * FROM hotel_bookings_validation ORDER BY ts DESC LIMIT 100", engine)
    st.dataframe(recent_data)
    
    # Série temporal de cancelamentos usando data de chegada da reserva
    df_val_full = pd.read_sql(
        "SELECT arrival_date_year, arrival_date_month, arrival_date_day_of_month, is_canceled "
        "FROM hotel_bookings_validation",
        engine,
    )

    # Constrói uma coluna de data real
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12,
    }
    df_val_full["month_num"] = df_val_full["arrival_date_month"].map(month_map)
    df_val_full["date"] = pd.to_datetime(
        dict(
            year=df_val_full["arrival_date_year"],
            month=df_val_full["month_num"],
            day=df_val_full["arrival_date_day_of_month"],
        )
    )

    time_cancel = (
        df_val_full.groupby("date")["is_canceled"]
        .sum()
        .reset_index(name="canceladas")
    )

    st.subheader("Cancelamentos ao longo do tempo")
    st.line_chart(time_cancel.set_index("date"))


    
    # Gráficos lado a lado
    col1, col2 = st.columns(2)
    
    with col1:
        cancel_query = """
        SELECT 
            CASE WHEN is_canceled = 0 THEN 'Não cancelada' ELSE 'Cancelada' END as status,
            COUNT(*) as count 
        FROM hotel_bookings_validation 
        GROUP BY is_canceled
        """
        cancel_dist = pd.read_sql(cancel_query, engine)
        st.subheader("Distribuição das reservas")

        cancel_dist = cancel_dist.set_index('status')
        st.bar_chart(cancel_dist)  # sem transpor

    
    with col2:
        # Hotéis - manter vertical
        hotel_dist = pd.read_sql("SELECT hotel, COUNT(*) as count FROM hotel_bookings_validation GROUP BY hotel", engine)
        st.subheader("Tipos de hotel")
        st.bar_chart(hotel_dist.set_index('hotel'))


elif page == "Modelos & MLflow":
    st.subheader("Modelos e métricas")
    st.write("Aqui depois vamos puxar experimentos do MLflow e comparar RF, XGB, SVM, MLP.")

elif page == "Simular reserva":
    st.subheader("Simular nova reserva")
    hotel = st.selectbox("Tipo de hotel", ["City Hotel", "Resort Hotel"])
    lead_time = st.number_input("Lead time (dias)", min_value=0, max_value=365, value=30)
    adr = st.number_input("ADR (tarifa média diária)", min_value=0.0, value=100.0)
    adults = st.number_input("Número de adultos", min_value=1, max_value=4, value=2)

    if st.button("Calcular probabilidade de cancelamento"):
        st.info("Mais pra frente vamos conectar aqui com o modelo salvo no MLflow.")
