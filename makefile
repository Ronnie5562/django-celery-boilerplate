# Environment variables (can be overridden)
ENV_FILE ?= .env
DOCKER_COMPOSE_FILE ?= docker/docker-compose.yml
DOCKER_COMPOSE_DEV_FILE ?= docker/docker-compose.dev.yml
PROJECT_NAME ?= app
DJANGO_MANAGE := python3 app/manage.py

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Local Development
.PHONY: start
start: ## Start the Django development server
	@echo "Starting Django development server..."
	$(DJANGO_MANAGE) runserver

.PHONY: shell
shell: ## Open Django shell
	@echo "Opening Django shell..."
	$(DJANGO_MANAGE) shell

.PHONY: test
test: ## Run tests
	@echo "Running tests..."
	cd app && python3 manage.py test --parallel --keepdb --verbosity=2

.PHONY: lint
lint: ## Run code linter
	@echo "Running linter..."
	flake8 .

.PHONY: format
format: ## Format code
	@echo "Formatting code..."
	black .
	isort .

.PHONY: check
check: lint test ## Run all checks (lint + test)

# Database Operations
.PHONY: migrations
migrations: ## Create new migrations
	@echo "Creating migrations..."
	$(DJANGO_MANAGE) makemigrations

.PHONY: migrate
migrate: ## Apply migrations
	@echo "Applying migrations..."
	$(DJANGO_MANAGE) migrate

.PHONY: resetdb
resetdb: ## Reset database (#!DANGER: destroys data)
	@echo "Resetting database..."
	$(DJANGO_MANAGE) reset_db --noinput
	$(DJANGO_MANAGE) migrate
	$(DJANGO_MANAGE) createsuperuser

# Docker Operations
.PHONY: docker_shell
container_shell: ## Open a shell in the Django container
	@echo "Opening shell in Django container..."
	cd docker && \
	docker-compose run app bash

.PHONY: dev
dev: ## Start all containers in dev mode
	@echo "Starting containers in dev mode..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) -f $(DOCKER_COMPOSE_DEV_FILE) --env-file $(ENV_FILE) up

.PHONY: up
up: ## Start all containers in detached mode
	@echo "Starting containers..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) --env-file $(ENV_FILE) up -d

.PHONY: down
down: ## Stop and remove containers
	@echo "Stopping containers..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down

.PHONY: refresh
refresh: ## Refresh containers with updated environment variables
	@echo "Refreshing containers with updated environment..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down
	docker-compose -f $(DOCKER_COMPOSE_FILE) --env-file $(ENV_FILE) up -d

.PHONY: restart
restart: ## Restart specific services
	@echo "Restarting services..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) --env-file $(ENV_FILE) restart app redis celery celery-beat flower

.PHONY: build
build: ## Build Docker images
	@echo "Building images..."
	COMPOSE_BAKE=true docker-compose -f docker/docker-compose.yml --env-file $(ENV_FILE) build --no-cache

.PHONY: logs
logs: ## View container logs
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f

.PHONY: ps
ps: ## List containers
	docker-compose -f $(DOCKER_COMPOSE_FILE) ps

.PHONY: clean-docker
clean-docker: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down -v --rmi local
	docker system prune -f

# Production Operations
.PHONY: collectstatic
collectstatic: ## Collect static files
	@echo "Collecting static files..."
	$(DJANGO_MANAGE) collectstatic --noinput

.PHONY: superuser
superuser: ## Create superuser
	@echo "Creating superuser..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) --env-file $(ENV_FILE) exec app python3 manage.py createsuperuser

.PHONY: prod
prod: build up ## Build and start production environment

# Utility
.PHONY: clean
clean: ## Clean python cache files
	@echo "Cleaning python cache files..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
