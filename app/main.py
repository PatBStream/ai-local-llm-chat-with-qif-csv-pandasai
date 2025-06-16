# app/main.py
import os
import io
import logging
from typing import List

import pandas as pd
import pandasai as pai
from pandasai_litellm import LiteLLM
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from qif_manual import parse_qif
from ollama_llm import llm  # our LiteLLM instance

# — Logging setup —
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# — FastAPI & CORS —
app = FastAPI(
    title="QIF/CSV Chat Agent",
    version="2.0.0",
    description="Chat with your CSV or QIF data using PandasAI v3 + LiteLLM (Ollama)",
)
origins = os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# — Configure PandasAI to use our LiteLLM —
# turn off randomness for deterministic results
pai.config.set({"llm": llm, "temperature": 0})

# — In-memory storage for raw & semantic DataFrames —
df_storage: dict[str, pd.DataFrame] = {}
pai_df_storage: dict[str, pai.DataFrame] = {}
df = None  # Initialize as a global variable

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
        logger.info("Loading CSV file: %s", file.filename)
        # Read the CSV file into a Pandas DataFrame
        df = pd.read_csv(file.file)
        df_storage["df"] = df

        # Semantic DataFrame for PandasAI v3
        pai_df = pai.DataFrame(df)
        pai_df_storage["df"] = pai_df

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

        pai_df = pai.DataFrame(df)
        pai_df_storage["df"] = pai_df

        logger.info("Loaded QIF '%s' (%d rows)", file.filename, len(df))
        return UploadResponse(columns=df.columns.tolist(), rows=len(df))
    except Exception as e:
        logger.error("QIF parse error: %s", e)
        raise HTTPException(500, f"Unable to parse QIF: {e}")


@app.post("/chat", response_model=ChatResponse)
async def chat_query(question: str = Form(...)):
    pai_df = pai_df_storage.get("df")
    if pai_df is None:
        raise HTTPException(400, "No data uploaded. POST to /upload_csv or /upload_qif first.")
    if not question.strip():
        raise HTTPException(400, "Question must not be empty.")
    try:
        answer = pai_df.chat(question)
        logger.info("Chat question: '%s' | Answer: %s", question, answer)
        return ChatResponse(answer=str(answer))
    except Exception as e:
        logger.error("Chat error: %s", e)
        raise HTTPException(500, f"Failed to process question: {e}")


@app.get("/dataframe", response_model=DataFrameInfo)
async def get_dataframe(sample_rows: int = 5):
    df = df_storage.get("df")
    if df is None:
        raise HTTPException(400, "No data uploaded. POST to /upload_csv or /upload_qif first.")
    try:
        sample = df.head(sample_rows).to_dict(orient="records")
        return DataFrameInfo(columns=list(df.columns), sample=sample)
    except Exception as e:
        logger.error("Data preview error: %s", e)
        raise HTTPException(500, f"Failed to fetch dataframe preview: {e}")


@app.get("/records_by_payee", response_model=DataFrameInfo)
async def records_by_payee(payee: str = Query(..., description="Payee name to filter by"), sample_rows: int = 5):
    """
    Return records where the 'payee' column matches the given value (case-insensitive).
    """
    df = df_storage.get("df")
    if df is None:
        raise HTTPException(400, "No data uploaded. POST to /upload_csv or /upload_qif first.")
    if "Payee" not in df.columns:
        raise HTTPException(400, "'Payee' column not found in the data.")
    try:
        filtered = df[df["Payee"].str.lower() == payee.lower()]
        sample = filtered.to_dict(orient="records")
#        sample = filtered.head(sample_rows).to_dict(orient="records")

        return DataFrameInfo(columns=list(df.columns), sample=sample)
    except Exception as e:
        logger.error("Payee query error: %s", e)
        raise HTTPException(500, f"Failed to query by payee: {e}")
