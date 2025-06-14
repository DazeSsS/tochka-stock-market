revision:
	docker compose run --build --rm app alembic revision --autogenerate -m "$m"

migrate:
	docker compose run --build --rm app alembic upgrade head

drop:
	docker compose run --build --rm app python3 -m src.scripts.drop_db

populate:
	docker compose run --build --rm app python3 -m src.scripts.populate_db

db:
	docker compose up -d db

rebuild: build down up

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

start:
	docker compose start

stop:
	docker compose stop

restart:
	docker compose restart

prune:
	docker system prune