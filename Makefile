.PHONY: help up down build restart logs ps makemigrations migrate runserver shell createsuperuser

help:
	@echo "Docker:"
	@echo "  make up              - start db and redis in background"
	@echo "  make down            - stop containers"
	@echo "  make build           - build docker images"
	@echo "  make restart         - restart containers"
	@echo "  make logs            - follow container logs"
	@echo "  make ps              - show container status"
	@echo "Django:"
	@echo "  make makemigrations  - create migrations (app=<name> for one app)"
	@echo "  make migrate         - apply migrations"
	@echo "  make runserver       - start dev server"
	@echo "  make shell           - Django shell"
	@echo "  make createsuperuser - create admin user"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart

logs:
	docker compose logs -f

ps:
	docker compose ps

makemigrations:
	uv run python manage.py makemigrations $(app)

migrate:
	uv run python manage.py migrate

runserver:
	uv run python manage.py runserver

shell:
	uv run python manage.py shell

createsuperuser:
	uv run python manage.py createsuperuser