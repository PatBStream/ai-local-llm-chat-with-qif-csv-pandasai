import streamlit as st
import requests
import logging
import os
import pandas as pd

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamlit_app")
API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="QIF/CSV Chat Agent", layout="wide")
st.title("QIF/CSV Chat Agent")

# --- Session state for upload status ---
if "csv_uploaded" not in st.session_state:
    st.session_state.csv_uploaded = False
if "upload_response" not in st.session_state:
    st.session_state.upload_response = None

# --- File uploader ---
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file and not st.session_state.csv_uploaded:
    files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
    try:
        logger.info(f"Uploading file: {uploaded_file.name}")
        response = requests.post(f"{API_URL}/upload_csv", files=files)
        if response.ok:
            st.session_state.csv_uploaded = True
            st.session_state.upload_response = response.json()
            st.success(f"CSV '{uploaded_file.name}' uploaded successfully!")
            logger.info(f"Upload successful: {uploaded_file.name}")
        else:
            st.error(f"Upload failed: {response.text}")
            logger.error(f"Upload failed: {response.text}")
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        logger.exception("Exception during file upload")

# --- Show DataFrame info if uploaded ---
if st.session_state.csv_uploaded and st.session_state.upload_response:
    st.subheader("DataFrame Info")
    st.write("Columns:", st.session_state.upload_response.get("columns", []))
    st.write("Rows:", st.session_state.upload_response.get("rows", 0))

# --- Chat interface ---
if st.session_state.csv_uploaded:
    st.subheader("Ask a question about your data")
    question = st.text_input("Question")
    if st.button("Ask") and question.strip():
        try:
            logger.info(f"Submitting question: {question}")
            response = requests.post(f"{API_URL}/chat",data={"question": question},timeout=120)
            if response.ok:
                answer = response.json().get("answer", "")
                st.success("Answer:")
                st.write(answer)
                # Try to parse answer as a table (CSV or markdown), else display as text
                try:
                    # Try parsing as CSV
                    df = pd.read_csv(pd.compat.StringIO(answer))
                    st.dataframe(df)
                except Exception:
                    try:
                        # Try parsing as markdown table
                        df = pd.read_table(pd.compat.StringIO(answer), sep="|", engine="python")
                        st.dataframe(df)
                    except Exception:
                        # Fallback: display as plain text
                        st.write(answer)
                logger.info("Received answer from /chat endpoint")
            else:
                st.error(f"Error: {response.text}")
                logger.error(f"Chat endpoint error: {response.text}")
        except Exception as e:
            st.error(f"Error submitting question: {e}")
            logger.exception("Exception during chat request")

# --- Reset option ---
if st.session_state.csv_uploaded:
    if st.button("Reset and upload a new file"):
        st.session_state.csv_uploaded = False
        st.session_state.upload_response = None
        st.experimental_rerun()