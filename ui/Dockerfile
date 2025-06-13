# ui/Dockerfile
FROM python:3.12.2-slim

WORKDIR /ui

# Copy the Streamlit app
COPY streamlit_app.py ./

# Install Streamlit + requests
RUN pip install --no-cache-dir streamlit requests

# Expose the default Streamlit port
EXPOSE 8501

# Launch Streamlit in JSON-array form (no stray tokens)
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
