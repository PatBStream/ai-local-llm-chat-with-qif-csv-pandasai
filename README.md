# AI Local LLM Chat with QIF/CSV via PandasAI

Background:  A locally hosted website using Docker and your LLM, to "chat" with your QIF/CSV files.

This repository contains a minimal FastAPI backend and Streamlit user interface for chatting with data contained in CSV or QIF files.  It uses the [PandasAI](https://pypi.org/project/pandasai/#description) library and a local language model served by [Ollama](https://ollama.com/) to answer questions about your data without relying on external services.

**Key features**

- Upload CSV or QIF files and convert them into a `pandas` DataFrame.
- Ask natural language questions about the uploaded data.
- All model inference happens locally through Ollama; no internet access is required after downloading the model.
- Docker setup for reproducible local runs.

## Project layout

```
.
├── Dockerfile            # Backend container image
├── docker-compose.yml    # Runs backend and Streamlit UI together
├── app/                  # FastAPI application
│   ├── main.py           # API endpoints
│   ├── ollama_llm.py     # PandasAI adapter for Ollama
│   ├── qif_manual.py     # Simple QIF parser
│   └── requirements.txt  # Python dependencies
└── ui/
    ├── Dockerfile        # Image for Streamlit interface
    └── streamlit_app.py  # Front‑end application
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An instance of Ollama running on the host machine with a model pulled (for example `phi4-mini:3.8b` or `llama3.1:8b`).

## Setup

1. **Start Ollama.** Ensure the service is running on the host at `http://localhost:11434` and that your desired model is pulled.

2. **Build and start the containers.** From the repository root, run:

   ```bash
   docker compose up --build
   ```

   This builds the FastAPI backend and the Streamlit UI. The backend container communicates with the host's Ollama instance.

3. **Access the UI.** Once the containers are running, open [http://localhost:8501](http://localhost:8501) in your browser.

## Usage

1. **Upload a file.** In the web interface, choose a `.csv` or `.qif` file. The server parses the file into a DataFrame.
2. **Ask questions.** After uploading, enter a natural‑language question about the data. Examples:
   - "What was the average transaction amount in 2023?"
   - "Show the total by category."
3. **View the answer.** The response from the model is displayed directly in the interface.

The backend exposes the following API endpoints if you wish to integrate with other tools:

- `POST /upload_csv` – upload a CSV file
- `POST /upload_qif` – upload a QIF file
- `POST /chat` – send a question about the uploaded data
- `GET /dataframe` – preview columns and sample rows from the uploaded data

### Example: preview the DataFrame

```bash
curl "http://localhost:8000/dataframe?sample_rows=5"
```

This returns JSON with a `columns` list and a `sample` array of rows.

Environment variables allow changing the target Ollama URL and CORS origins (see `docker-compose.yml` and `app/main.py`).

## Development notes

All Python dependencies are listed in `app/requirements.txt`. When building the Docker image these are installed with ARM64‑compatible versions of `numpy` and `pandas`.

Tests and linting tools (pytest, flake8, black, isort) are included in the requirements file but are not run automatically in the containers.

## License

This project was generated for demonstration purposes. Use at your own risk.
