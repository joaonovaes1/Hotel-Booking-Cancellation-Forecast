# **Hotel-Booking-Cancellation-Forecast**

Pipeline End-to-End: IoT → Data Lake → Banco → Modelagem → MLflow → Dashboard

Este projeto implementa um pipeline completo de **Engenharia de Dados, IoT e Machine Learning** para previsão de cancelamento de reservas de hotel.
O fluxo integra **ThingsBoard**, **FastAPI**, **MinIO**, **JupyterLab**, **MLflow**, além da reprodução e expansão de um paper de referência na área.

O objetivo final é criar uma solução **automatizada e reprodutível** que:

* coleta dados brutos via IoT,
* armazena e organiza em um data lake,
* processa e modela,
* versiona modelos,
* e exibe resultados em dashboards consolidados.

---

# 👥 Equipe


| Nome                  | E-mail                                                                  | GitHub                                |
| --------------------- | ----------------------------------------------------------------------- | ------------------------------------- |
| **João Marcelo**      | [jmnfa@cesar.school](mailto:jmnfa@cesar.school)                         | —                                     |
| **Vinicius Ventura**  | [vini.ventura999@gmail.com](mailto:vini.ventura999@gmail.com)           | —                                     |
| **Gabriel Magalhães** | [gabrielgrmagalhaes@outlook.com](mailto:gabrielgrmagalhaes@outlook.com) | —                                     |
| **Arthur Freire**     | [arthurduartefreire@gmail.com](mailto:arthurduartefreire@gmail.com)     | —                                     |
| **Igor Wanderley**    | [igorfwds@hotmail.com](mailto:igorfwds@hotmail.com)                     | —                                     |
| **Laura Vidal**       | [lauravidal@outlook.com](mailto:lauravidal@outlook.com)                 | —                                     |


Instituição: Instituição: CESAR School
Disciplina: Aprendizado de Máquina - 2025.2

---

# **Arquitetura do Projeto**

Todo o pipeline roda via **Docker Compose**, orquestrando os seguintes serviços:

### **1. Script Python → ThingsBoard**

Envia dados simulados ou coletados de sensores para o ThingsBoard via MQTT/HTTP.

### **2. FastAPI → Bucket**

API responsável por consumir dados do ThingsBoard e armazená-los no bucket “raw” do Data Lake.

### **3. Bucket → MinIO (S3)**

O bucket armazena os dados brutos e processados.
A API ou scripts internos movem os dados para estruturas organizadas dentro do MinIO.

### **4. MinIO → JupyterLab**

Notebooks utilizam o MinIO como fonte única de verdade para análise exploratória, limpeza, preparação e modelagem.

### **5. Reprodução do Paper + Contribuições**

A pipeline inclui um notebook dedicado à reprodução do paper utilizado como referência, seguido das melhorias e extensões propostas pelo time.

### **6. Versionamento de Modelos no MLflow**

Todos os experimentos e métricas são armazenados no MLflow Tracking Server.

### **7. Dashboard final**

Dashboard unificado consumindo:

* dados brutos do ThingsBoard (tempo real),
* previsões dos modelos registrados no MLflow.

---

# **Estrutura de Pastas**

```
/
├── api/                                # FastAPI responsável por enviar dados ao bucket/MinIO
│   ├── __pycache__/                    # Cache interno do Python
│   ├── main.py                         # API principal (ingestão / integração ThingsBoard -> Bucket)
│   └── data/
│       └── hotel_bookings.csv          # Dataset base utilizado pela API
│
├── iot/
│   └── send_csv_to_thingsboard.py      # Script Python que envia dados CSV diretamente ao ThingsBoard
│
├── mlruns/                             # Diretório gerado automaticamente pelo MLflow Tracking
│   ├── .trash/                         # Experimentos deletados
│   ├── 0/                              # Experimento "Default"
│   ├── <run_id_1>/                     # Execuções rastreadas
│   ├── <run_id_2>/
│   └── models/                         # Artefatos de modelos versionados
│
├── notebooks/                          # Notebooks Jupyter para análise, modelagem e paper
│   ├── 01_eda_baseline.ipynb           # Análise exploratória inicial
│   └── 02_deep_analysis.ipynb          # Análise aprofundada, testes e modelagem
│
├── src/
│   ├── mlflow_experiments/             # Scripts de experimentação e registro no MLflow
│   └── validate_neondb.py              # Validação do banco NeonDB / infraestrutura externa (se aplicável)
│
├── venv/                               # Ambiente virtual Python usado no VS Code
│   ├── Include/
│   ├── Lib/
│   ├── Scripts/
│   └── etc/
│
├── .env                                # Variáveis de ambiente (ThingsBoard, Bucket, MLflow, MinIO)
├── .gitignore
├── LICENSE
├── README.md                           # Documentação do projeto
└── requirements.txt                    # Dependências Python
```

# **Como Executar o Projeto**

Abaixo está o guia completo para levantar a infraestrutura, coletar dados, treinar modelos e visualizar resultados.

---

## **Pré-requisitos**

* Docker Desktop instalado e rodando
* Git (opcional)
* Python 3.9+ (caso execute o script ThingsBoard fora do Docker)

---

# **Passo 1: Subir a Infraestrutura (Docker)**

Na raiz do projeto (onde está o `docker-compose.yml`):

```bash
docker-compose up -d --build
```

Verifique se todos os containers estão ativos:

```bash
docker ps
```

---

# **Passo 2: Enviar Dados para o ThingsBoard**

Execute o script localizado em `/scripts`:

```bash
python scripts/send_to_thingsboard.py
```

Certifique-se de ter configurado corretamente o **Device Token** do ThingsBoard.

Painel do ThingsBoard:
**[http://localhost:8080](http://localhost:8080)**

---

# **Passo 3: Ingestão de Dados (FastAPI → Bucket)**

Acesse a documentação da API:

**[http://localhost:8000/docs](http://localhost:8000/docs)**

Use o endpoint responsável por capturar as métricas do ThingsBoard e enviá-las para o bucket.

Exemplo:
`POST /ingest/thingsboard`

Se receber 200 OK → dados armazenados com sucesso.

---

# **Passo 4: Armazenamento no MinIO**

Acesse o console:

**[http://localhost:9001](http://localhost:9001)**
Usuário: `minioadmin`
Senha: `minioadmin`

Verifique se os dados brutos foram armazenados no bucket correspondente.

---

# **Passo 5: Notebooks (EDA, Modelagem e Paper)**

Acesse:

**[http://localhost:8888](http://localhost:8888)**

Abra os notebooks em `/notebooks`:

* `eda_and_cleaning.ipynb`
* `model_training.ipynb`
* `paper_reproduction.ipynb`
* `contributions.ipynb`

Executar tudo sequencialmente.

### Saídas esperadas:

* Gráficos e relatórios em `/notebooks/outputs`
* Modelos registrados no MLflow
* Dados tratados enviados ao MinIO

---

# **Passo 6: Versionamento no MLflow**

Acesse:

**[http://localhost:5000](http://localhost:5000)**

Aqui você poderá:

* acompanhar métricas,
* comparar experimentos,
* armazenar modelos,
* gerar artefatos.

Experimento principal:
**Hotel_Booking_Cancellation_Forecast**

---

# **Passo 7: Dashboard Final**

O dashboard integra:

* dados brutos diretamente do ThingsBoard
* previsões dos modelos (via MLflow ou API)
* visualizações agregadas
* métricas de cancelamento

Acesse a interface no container correspondente (ex.: Streamlit ou Grafana, dependendo da implementação).

---

# **Encerrando a Execução**

Para parar tudo:

```bash
docker-compose down
```
