.PHONY: up down build restart logs clean test init import-data

# Запуск всех сервисов
up:
	docker-compose up -d

# Остановка всех сервисов
down:
	docker-compose down

# Пересборка и запуск
build:
	docker-compose up -d --build

# Перезапуск
restart:
	docker-compose restart

# Просмотр логов
logs:
	docker-compose logs -f

# Очистка (осторожно!)
clean:
	docker-compose down -v
	docker system prune -f

# Запуск тестов
test:
	docker-compose exec api-gateway curl -f http://localhost:8000/health
	docker-compose exec api-gateway curl -f http://localhost:8000/api/auth/health
	docker-compose exec api-gateway curl -f http://localhost:8000/api/cv_processing/health
	docker-compose exec api-gateway curl -f http://localhost:8000/api/geocoding/health

# Инициализация БД
init:
	docker-compose down postgres
	rm -rf databases/postgres
	mkdir -p databases/postgres
	docker-compose up -d postgres
	sleep 20
	docker-compose exec postgres psql -U admin -d geo_photo_db -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"

# Импорт данных
import-data:
	python scripts/import_existing_data.py

# Запуск в production режиме
production:
	docker-compose --profile production up -d

# Просмотр статуса
status:
	docker-compose ps
	docker-compose exec api-gateway curl -s http://localhost:8000/health | jq .

# Backup базы данных
backup:
	mkdir -p backups
	docker-compose exec postgres pg_dump -U admin -d geo_photo_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

# Восстановление из backup
restore:
	@if [ -z "$(file)" ]; then \
		echo "Usage: make restore file=backups/backup_YYYYMMDD_HHMMSS.sql"; \
		exit 1; \
	fi
	docker-compose exec -T postgres psql -U admin -d geo_photo_db < $(file)