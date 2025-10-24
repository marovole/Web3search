web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
worker: cd backend && celery -A app.tasks.celery_app worker --loglevel=info
beat: cd backend && celery -A app.tasks.celery_app beat --loglevel=info
