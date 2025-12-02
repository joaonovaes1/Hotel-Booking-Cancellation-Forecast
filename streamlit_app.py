import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hotel Booking Cancellation", layout="wide")


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

    # ===================== MÉTRICA + TABELA =====================
    st.metric("Total registros validação", 18021)

    recent_data = pd.read_sql(
        "SELECT * FROM hotel_bookings_validation ORDER BY ts DESC LIMIT 100",
        engine,
    )
    st.dataframe(recent_data, use_container_width=True)

    # ===================== SÉRIE TEMPORAL =====================
    df_val_full = pd.read_sql(
        """
        SELECT 
            arrival_date_year, 
            arrival_date_month, 
            arrival_date_day_of_month, 
            is_canceled,
            hotel
        FROM hotel_bookings_validation
        """,
        engine,
    )

    
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12,
    }
    if df_val_full["arrival_date_month"].dtype == "object":
        df_val_full["month_num"] = df_val_full["arrival_date_month"].map(month_map)
    else:
        df_val_full["month_num"] = df_val_full["arrival_date_month"]

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

    fig_time = px.line(
        time_cancel,
        x="date",
        y="canceladas",
        title="Cancelamentos diários",
    )

    fig_time.update_traces(line_color="#00C0F2", line_width=2)
    fig_time.update_layout(
        showlegend=False,
        xaxis_title="Data",
        yaxis_title="Reservas canceladas",
        template="plotly_dark",
        hovermode="x unified",
        height=350,
    )

    st.plotly_chart(fig_time, use_container_width=True)

    # ===================== GRÁFICOS DE DISTRIBUIÇÃO =====================
    col1, col2 = st.columns(2)

    
    with col1:
        cancel_query = """
        SELECT 
            CASE WHEN is_canceled = 0 THEN 'Não cancelada' ELSE 'Cancelada' END AS status,
            COUNT(*) AS count
        FROM hotel_bookings_validation
        GROUP BY is_canceled
        """
        cancel_dist = pd.read_sql(cancel_query, engine)

        fig_cancel = px.bar(
            cancel_dist,
            x="count",
            y="status",
            orientation="h",
            title="Distribuição das reservas",
            color="status",
            color_discrete_map={
                "Cancelada": "#00C0F2",      
                "Não cancelada": "#7DD3FC",  
            },
        )
        fig_cancel.update_layout(
            template="plotly_dark",
            showlegend=False,
            xaxis_title="Quantidade",
            yaxis_title="",
            height=350,
        )
        st.plotly_chart(fig_cancel, use_container_width=True)

    # Tipos de hotel
    with col2:
        hotel_query = """
        SELECT 
            hotel,
            COUNT(*) AS count
        FROM hotel_bookings_validation
        GROUP BY hotel
        """
        hotel_dist = pd.read_sql(hotel_query, engine)

        fig_hotel = px.bar(
            hotel_dist,
            x="count",
            y="hotel",
            orientation="h",
            title="Tipos de hotel",
            color="hotel",
            color_discrete_map={
                "City Hotel": "#00C0F2",
                "Resort Hotel": "#7DD3FC",
            },
        )
        fig_hotel.update_layout(
            template="plotly_dark",
            showlegend=False,
            xaxis_title="Quantidade",
            yaxis_title="",
            height=350,
        )
        st.plotly_chart(fig_hotel, use_container_width=True)



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
