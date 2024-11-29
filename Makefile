ifneq (,$(wildcard ./.env))
	include .env
	export
	ENV_FILE_PARAM = --env-file .env
endif

build:
	sudo docker-compose up --build -d --remove-orphans

up:
	sudo docker-compose up -d

down:
	sudo docker-compose down

logs:
	sudo docker-compose logs

migrate:
	sudo docker-compose exec api python3 manage.py migrate --noinput

makemigrations:
	sudo docker-compose exec api python3 manage.py makemigrations

superuser:
	sudo docker-compose exec api python3 manage.py createsuperuser

app:
	sudo docker-compose exec api python3 manage.py startapp

down-v:
	sudo docker-compose down -v

volume:
	sudo docker volume inspect backend_postgres_data

shell:
	sudo docker-compose exec api python3 manage.py shell