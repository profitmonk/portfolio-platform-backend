# start.py - using Railway's service name
import os

# Railway sets RAILWAY_SERVICE_NAME automatically
service_name = os.getenv("RAILWAY_SERVICE_NAME", "")

if "worker" in service_name.lower() or "price" in service_name.lower():
    print("🔧 Starting worker service...")
    os.system("python -m app.jobs.daily_price_update.py")
else:
    print("🌐 Starting web service...")
    os.system("python reset_migrations.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT")
