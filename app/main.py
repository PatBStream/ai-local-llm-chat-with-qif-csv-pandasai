# app/main.py

import os
import io
import logging
from typing import List

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Updated imports for current PandasAI API
from pandasai import SmartDataframe
from ollama_llm import OllamaLLM

from qif_manual import parse_qif

# — Logging setup —
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# — FastAPI & CORS —
app = FastAPI(
    title="QIF/CSV Chat Agent",
    version="1.0.0",
    description="Chat with your CSV or QIF data using PandasAI + local Ollama LLM",
)
origins = os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# — Configure LLM for Ollama —
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

# Configure the LLM to use Ollama
llm = OllamaLLM(
    api_base=OLLAMA_URL,
    #    model="phi4-mini:3.8b",
    model="llama3.1:8b",  # Example model, adjust as needed
)

# — In-memory DataFrame storage —
df_storage: dict[str, pd.DataFrame] = {}
smart_df_storage: dict[str, SmartDataframe] = {}


class UploadResponse(BaseModel):
    columns: List[str]
    rows: int


class ChatResponse(BaseModel):
    answer: str


class DataFrameInfo(BaseModel):
    columns: List[str]
    sample: List[dict]


@app.post("/upload_csv", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Expected a .csv file")
    try:
        df = pd.read_csv(file.file)
        df_storage["df"] = df
        # Create SmartDataframe with the LLM
        smart_df = SmartDataframe(df, config={"llm": llm}, verbose=True)
        smart_df_storage["smart_df"] = smart_df
        logger.info("Loaded CSV '%s' (%d rows)", file.filename, len(df))
        return UploadResponse(columns=df.columns.tolist(), rows=len(df))
    except Exception as e:
        logger.error("CSV parse error: %s", e)
        raise HTTPException(500, f"Unable to parse CSV: {e}")


@app.post("/upload_qif", response_model=UploadResponse)
async def upload_qif(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".qif"):
        raise HTTPException(400, "Expected a .qif file")
    try:
        raw = await file.read()
        text = raw.decode("utf-8", errors="ignore")
        df = parse_qif(io.StringIO(text))
        df_storage["df"] = df
        # Create SmartDataframe with the LLM
        smart_df = SmartDataframe(df, config={"llm": llm})
        smart_df_storage["smart_df"] = smart_df
        logger.info("Loaded QIF '%s' (%d rows)", file.filename, len(df))
        return UploadResponse(columns=df.columns.tolist(), rows=len(df))
    except Exception as e:
        logger.error("QIF parse error: %s", e)
        raise HTTPException(500, f"Unable to parse QIF: {e}")


@app.post("/chat", response_model=ChatResponse)
async def chat_query(question: str = Form(...)):
    smart_df = smart_df_storage.get("smart_df")
    if smart_df is None:
        raise HTTPException(
            400, "No data uploaded. POST to /upload_csv or /upload_qif first."
        )
    if not question.strip():
        raise HTTPException(400, "Question must not be empty.")
    try:
        # Use the new SmartDataframe.chat() method
        answer = smart_df.chat(question)
        return ChatResponse(answer=str(answer))
    except Exception as e:
        logger.error("Chat error: %s", e)
        raise HTTPException(500, f"Failed to process question: {e}")


@app.get("/dataframe", response_model=DataFrameInfo)
async def get_dataframe(sample_rows: int = 5):
    """Return columns and a sample of rows from the uploaded DataFrame."""
    df = df_storage.get("df")
    if df is None:
        raise HTTPException(
            400,
            "No data uploaded. POST to /upload_csv or /upload_qif first.",
        )
    try:
        sample = df.head(sample_rows).to_dict(orient="records")
        return DataFrameInfo(columns=list(df.columns), sample=sample)
    except Exception as e:
        logger.error("Data preview error: %s", e)
        raise HTTPException(500, f"Failed to fetch dataframe preview: {e}")
