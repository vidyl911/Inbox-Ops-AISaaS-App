Set-Location "C:\Desktop\InboxOps_SaaS_App"

& ".\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --app-dir backend
