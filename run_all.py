
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     Custom launcher     *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------



# run_all.py
import subprocess, sys, time

py = sys.executable  # uses the venv python when activated

subprocess.Popen([py, "-m", "uvicorn", "backend.main:app", "--reload"])
time.sleep(2)
subprocess.Popen([py, "-m", "streamlit", "run", "frontend/app.py"])



#
# streamlit run frontend/app.py
#
#
# uvicorn backend.main:app --reload
#