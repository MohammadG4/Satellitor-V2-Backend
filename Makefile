SHELL := /bin/sh

PROJECT=Satellitor-V2

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200 web

ps:
	docker compose ps

migrate:
	docker compose exec web python Satellitor/manage.py migrate

makesuper:
	docker compose exec -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_PASSWORD=admin -e DJANGO_SUPERUSER_EMAIL=admin@example.com web python Satellitor/create_superuser.py

shell:
	docker compose exec web python Satellitor/manage.py shell

collectstatic:
	docker compose exec web python Satellitor/manage.py collectstatic --noinput

makemigrations:
	docker compose exec web python Satellitor/manage.py makemigrations



