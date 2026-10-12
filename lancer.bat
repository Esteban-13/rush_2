@echo off
rem Lance l'application en local et ouvre le navigateur. Fermer cette fenetre arrete l'application.
cd /d %~dp0
set PY=python
if exist venv\Scripts\python.exe set PY=venv\Scripts\python.exe
%PY% -c "import streamlit, xlsxwriter" 2>nul
if errorlevel 1 (
    echo Installation des bibliotheques, merci de patienter...
    %PY% -m pip install -r requirements.txt
)
start "" /b cmd /c "timeout /t 5 >nul & start http://localhost:8501"
%PY% -m streamlit run app\app.py --server.headless true --server.port 8501
pause
