#!/usr/bin/env python3
"""
Hotel Booking Cancellation - Baseline Paper (Resort + City Hotel)
Reprodução dos modelos do paper original com MLflow tracking
"""

import mlflow
import mlflow.sklearn
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')




def load_data():
    """Carrega dados do NeonDB"""
    load_dotenv()
    database_url = os.getenv("NEON_DATABASE_URL")
    engine = create_engine(database_url)
    query = "SELECT * FROM hotel_bookings"
    return pd.read_sql(query, engine)

def fix_date_columns(df_raw):
    """Converte colunas de data para dayofyear"""
    df_fixed = df_raw.copy()
    for col in df_fixed.select_dtypes(include=['object']).columns:
        if df_fixed[col].nunique() > 20:
            try:
                conv = pd.to_datetime(df_fixed[col], errors='coerce')
                if conv.notna().sum() > 0:
                    print(f" Convertendo {col} para dayofyear...")
                    df_fixed[col] = conv.dt.dayofyear
            except Exception:
                print(f" Removendo {col}")
                df_fixed = df_fixed.drop(columns=[col])
    return df_fixed

def metrics_paper(y_true, y_pred):
    """Métricas do paper"""
    oa = float(accuracy_score(y_true, y_pred))
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average=None, labels=[1, 0]
    )
    return {
        "OA": float(oa),
        "P_1": float(precision[0]),
        "R_1": float(recall[0]),
        "F1_1": float(f1[0]),
        "P_0": float(precision[1]),
        "R_0": float(recall[1]),
        "F1_0": float(f1[1]),
    }

def train_models_for_hotel(df, hotel_name):
    """Treina todos os modelos para um hotel específico"""
    print(f"\n Processando {hotel_name}...")
    
    # Filtra dados do hotel
    df_hotel = df[df["hotel"] == hotel_name].copy()
    print(hotel_name, df_hotel.shape)
    
    y = df_hotel['is_canceled']
    cols_to_drop = ['is_canceled', 'reservation_status', 'reservation_status_date']
    X = df_hotel.drop(columns=cols_to_drop)
    
    print("y value_counts:", y.value_counts())
    print("X shape:", X.shape)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    # Fix datas
    X_train_fixed = fix_date_columns(X_train)
    X_test_fixed = fix_date_columns(X_test)
    
    # Preprocessador
    continuous_cols = X_train_fixed.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X_train_fixed.select_dtypes(include=['object']).columns.tolist()
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', MinMaxScaler(), continuous_cols),
            ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), categorical_cols)
        ]
    )
    
    X_train_processed = preprocessor.fit_transform(X_train_fixed)
    X_test_processed = preprocessor.transform(X_test_fixed)
    
    print("X_train_processed:", X_train_processed.shape)
    print("X_test_processed:", X_test_processed.shape)
    
    # ==================== RANDOM FOREST ====================
    with mlflow.start_run(run_name=f"{hotel_name}_RandomForest"):
        rf_param_grid = {
            'n_estimators': [200],
            'max_depth': [10, 15],
            'min_samples_split': [5, 10],
            'min_samples_leaf': [2, 4],
            'bootstrap': [True],
            'class_weight': ['balanced']
        }
        
        rf_grid = GridSearchCV(
            RandomForestClassifier(random_state=42, n_jobs=-1),
            rf_param_grid, cv=3, n_jobs=-1, verbose=1
        )
        rf_grid.fit(X_train_processed, y_train)
        rf_best = rf_grid.best_estimator_
        
        mlflow.log_params(rf_grid.best_params_)
        mlflow.log_param("model_type", "RandomForest")
        mlflow.log_param("hotel", hotel_name)
        
        y_rf_train = rf_best.predict(X_train_processed)
        y_rf_test = rf_best.predict(X_test_processed)
        
        m_train_rf = metrics_paper(y_train, y_rf_train)
        m_test_rf = metrics_paper(y_test, y_rf_test)
        
        # Log métricas
        for k, v in m_test_rf.items():
            mlflow.log_metric(f"test_{k}", v)
        for k, v in m_train_rf.items():
            mlflow.log_metric(f"train_{k}", v)
        
        mlflow.sklearn.log_model(rf_best, "rf_model")
        print(f" RF {hotel_name} - OA teste: {m_test_rf['OA']:.3f}")
    
    # ==================== XGBOOST ====================
    with mlflow.start_run(run_name=f"{hotel_name}_XGBoost"):
        xgb_param_grid = {
            'n_estimators': [300, 500],
            'max_depth': [3, 6],
            'learning_rate': [0.05, 0.1],
            'subsample': [0.8, 1.0],
            'colsample_bytree': [0.8, 1.0]
        }
        
        xgb_grid = GridSearchCV(
            XGBClassifier(eval_metric='logloss', random_state=42, n_jobs=-1),
            xgb_param_grid, cv=3, n_jobs=-1, verbose=1
        )
        xgb_grid.fit(X_train_processed, y_train)
        xgb_best = xgb_grid.best_estimator_
        
        mlflow.log_params(xgb_grid.best_params_)
        mlflow.log_param("model_type", "XGBoost")
        mlflow.log_param("hotel", hotel_name)
        
        y_xgb_train = xgb_best.predict(X_train_processed)
        y_xgb_test = xgb_best.predict(X_test_processed)
        
        m_train_xgb = metrics_paper(y_train, y_xgb_train)
        m_test_xgb = metrics_paper(y_test, y_xgb_test)
        
        for k, v in m_test_xgb.items():
            mlflow.log_metric(f"test_{k}", v)
        for k, v in m_train_xgb.items():
            mlflow.log_metric(f"train_{k}", v)
        
        mlflow.xgboost.log_model(xgb_best, "xgb_model")
        print(f" XGB {hotel_name} - OA teste: {m_test_xgb['OA']:.3f}")
    
    # ==================== SVM ====================
    with mlflow.start_run(run_name=f"{hotel_name}_SVM"):
        imputer = SimpleImputer(strategy='median')
        X_train_svm = imputer.fit_transform(X_train_processed)
        X_test_svm = imputer.transform(X_test_processed)
        
        svm_param_grid = {
            'C': [1, 5],
            'gamma': ['scale', 0.1, 0.01],
            'kernel': ['rbf']
        }
        
        svm_grid = GridSearchCV(
            SVC(random_state=42),
            svm_param_grid, cv=3, n_jobs=-1, verbose=1
        )
        svm_grid.fit(X_train_svm, y_train)
        svm_best = svm_grid.best_estimator_
        
        mlflow.log_params(svm_grid.best_params_)
        mlflow.log_param("model_type", "SVM")
        mlflow.log_param("hotel", hotel_name)
        
        y_svm_train = svm_best.predict(X_train_svm)
        y_svm_test = svm_best.predict(X_test_svm)
        
        m_train_svm = metrics_paper(y_train, y_svm_train)
        m_test_svm = metrics_paper(y_test, y_svm_test)
        
        for k, v in m_test_svm.items():
            mlflow.log_metric(f"test_{k}", v)
        for k, v in m_train_svm.items():
            mlflow.log_metric(f"train_{k}", v)
        
        mlflow.sklearn.log_model(svm_best, "svm_model")
        print(f" SVM {hotel_name} - OA teste: {m_test_svm['OA']:.3f}")

def main():
    """Executa experimentos para Resort e City Hotel"""
    # Config MLflow
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("hotel_booking_cancellation_paper_baseline")
    
    # Carrega dados
    print(" Carregando dados do NeonDB...")
    df = load_data()
    
    # Treina para os dois hotéis
    train_models_for_hotel(df, "Resort Hotel")
    train_models_for_hotel(df, "City Hotel")
    
    print("\n Todos experimentos baseline do paper logados no MLflow!")

if __name__ == "__main__":
    main()
