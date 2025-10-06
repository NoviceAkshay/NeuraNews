
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     Custom launcher     *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------



import subprocess
import time

# Start backend
subprocess.Popen(["uv", "run", "uvicorn", "backend.main:app", "--reload"])

# Small delay to make sure backend starts first
time.sleep(2)

# Start frontend
subprocess.Popen(["uv", "run", "streamlit", "run", "frontend/app.py"])
