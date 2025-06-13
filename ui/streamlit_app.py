# ui/streamlit_app.py
import os
import streamlit as st
import requests
from requests.exceptions import RequestException

st.set_page_config(page_title="QIF/CSV Chat", layout="centered")
st.title("Chat with Your QIF/CSV Data")

backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

def upload(file):
    endpoint = "/upload_csv" if file.name.lower().endswith(".csv") else "/upload_qif"
    try:
        files = {"file": (file.name, file, file.type)}
        resp = requests.post(f"{backend_url}{endpoint}", files=files, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except RequestException as e:
        st.error(f"Upload failed: {e}")
        return None

uploaded = False
meta = None

f = st.file_uploader("Upload a CSV or QIF file", type=["csv", "qif"])
if f:
    meta = upload(f)
    if meta:
        uploaded = True
        st.success(f"Loaded {meta['rows']} rows; columns: {meta['columns']}")

if uploaded:
    q = st.text_input("Ask a question about the data:")
    if st.button("Ask") and q:
        try:
            resp = requests.post(f"{backend_url}/chat", data={"question": q}, timeout=60)
            resp.raise_for_status()
            st.write("**Answer:**", resp.json().get("answer", ""))
        except RequestException as e:
            st.error(f"Failed to get answer: {e}")
