#!/bin/bash

# Default port
PORT=${PORT:-8000}  # Defaults to 8000 if PORT is not set

# Function to run flake8 checks
run_flake8_checks() {
  echo "Running flake8 checks..."
  flake8
  if [ $? -ne 0 ]; then
    echo "Flake8 checks failed. Exiting."
    exit 1
  fi
  echo "Flake8 checks passed!"
}

# Check the command passed to the script
if [ "$1" == "web" ]; then
  run_flake8_checks
  echo "Starting Daphne server on port $PORT..."
  daphne LaLouge.asgi:application --port "$PORT" --bind 0.0.0.0 -v2
elif [ "$1" == "celeryworker" ]; then
  run_flake8_checks
  echo "Starting Celery worker..."
  celery -A LaLouge worker --loglevel=info
elif [ "$1" == "celerybeat" ]; then
  run_flake8_checks
  echo "Starting Celery beat..."
  celery -A LaLouge beat --loglevel=info
else
  echo "Unknown command. Use 'web', 'celeryworker', or 'celerybeat'."
  exit 1
fi
