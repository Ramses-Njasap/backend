web: daphne LaLouge.asgi:application --port $PORT --bind 0.0.0.0 -v2
celeryworker: celery -A LaLouge worker --loglevel=info
celerybeat: celery -A LaLouge beat --loglevel=info

--------------------------------------------------------------
OR
--------------------------------------------------------------

web: ./run_service.sh web
celeryworker: ./run_service.sh celeryworker
celerybeat: ./run_service.sh celerybeat