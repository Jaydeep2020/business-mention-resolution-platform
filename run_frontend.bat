@echo off
echo Starting Business Mention Resolution Platform Streamlit UI...
.venv\Scripts\streamlit.exe run streamlit_app.py --server.port=8501 --server.address=127.0.0.1
pause
