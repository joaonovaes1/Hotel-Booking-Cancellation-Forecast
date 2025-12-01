from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np
import pandas as pd
import os
from sqlalchemy import create_engine
import mlflow
import mlflow.sklearn
from dotenv import load_dotenv
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
    df_fixed = df_raw.copy()
    for col in df_fixed.select_dtypes(include=['object']).columns:
        if df_fixed[col].nunique() > 20:
            try:
                conv = pd.to_datetime(df_fixed[col], errors='coerce')
                if conv.notna().sum() > 0:
                    print(f"Convertendo {col} para dayofyear...")
                    df_fixed[col] = conv.dt.dayofyear
            except Exception:
                print(f"Removendo {col}")
                df_fixed = df_fixed.drop(columns=[col])
    return df_fixed


def metrics_paper(y_true, y_pred):
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




def train_mlp_for_hotel(df, hotel_name):
    print(f"\nProcessando {hotel_name}...")

    # 1) Filtra hotel
    df_hotel = df[df["hotel"] == hotel_name].copy()
    print(hotel_name, df_hotel.shape)

    y = df_hotel['is_canceled']
    cols_to_drop = ['is_canceled', 'reservation_status', 'reservation_status_date']
    X = df_hotel.drop(columns=cols_to_drop)

    # 2) Split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
 
    
    X_train_fixed = fix_date_columns(X_train)
    X_test_fixed = fix_date_columns(X_test)

    # 4) Preprocessador numérico/categórico
    continuous_cols = X_train_fixed.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X_train_fixed.select_dtypes(include=['object']).columns.tolist()

    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', MinMaxScaler(), continuous_cols),
            ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), categorical_cols)
        ]
    )

    X_train_processed = preprocessor.fit_transform(X_train_fixed)
    X_test_processed = preprocessor.transform(X_test_fixed)

    # 5) Imputação para MLP
    from sklearn.impute import SimpleImputer
    from sklearn.neural_network import MLPClassifier
    from sklearn.model_selection import GridSearchCV

    imputer = SimpleImputer(strategy='median')
    X_train_mlp = imputer.fit_transform(X_train_processed)
    X_test_mlp = imputer.transform(X_test_processed)

    print("NaNs em X_train_mlp:", np.isnan(X_train_mlp).sum())
    print("NaNs em X_test_mlp :", np.isnan(X_test_mlp).sum())

    mlp_param_grid = {
        'hidden_layer_sizes': [(64,), (64, 32)],
        'activation': ['relu'],
        'solver': ['adam'],
        'alpha': [1e-4, 1e-3],
        'learning_rate_init': [0.001],
        'max_iter': [100],
        'batch_size': [256]
    }

    with mlflow.start_run(run_name=f"{hotel_name}_MLP"):
        mlp_grid = GridSearchCV(
            estimator=MLPClassifier(random_state=42),
            param_grid=mlp_param_grid,
            cv=3,
            n_jobs=-1,
            verbose=1
        )

        mlp_grid.fit(X_train_mlp, y_train)
        mlp_best = mlp_grid.best_estimator_
        print("MLP best:", mlp_grid.best_params_)

        # Log params
        mlflow.log_params(mlp_grid.best_params_)
        mlflow.log_param("model_type", "MLP")
        mlflow.log_param("hotel", hotel_name)

        # Predições
        y_mlp_train = mlp_best.predict(X_train_mlp)
        y_mlp_test = mlp_best.predict(X_test_mlp)

        m_train_mlp = metrics_paper(y_train, y_mlp_train)
        m_test_mlp = metrics_paper(y_test, y_mlp_test)

        print("MLP Treino:")
        for k, v in m_train_mlp.items():
            print(f"  {k}: {v:.3f}")
            mlflow.log_metric(f"train_{k}", v)

        print("\nMLP Teste:")
        for k, v in m_test_mlp.items():
            print(f"  {k}: {v:.3f}")
            mlflow.log_metric(f"test_{k}", v)

        mlflow.sklearn.log_model(mlp_best, "mlp_model")
        print(f"MLP {hotel_name} - OA teste: {m_test_mlp['OA']:.3f}")



def main():
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("hotel_booking_cancellation_contributions")

    load_dotenv()
    df = load_data()

    train_mlp_for_hotel(df, "Resort Hotel")
    train_mlp_for_hotel(df, "City Hotel")


if __name__ == "__main__":
    main()
