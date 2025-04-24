# Makefile

# Image name for the dev environment
IMAGE_NAME = cassandra-dev

# Default Docker build context is the .devcontainer folder
DOCKERFILE = .devcontainer/Dockerfile

# 1) Build the dev image
build:
	docker build -t $(IMAGE_NAME) -f $(DOCKERFILE) .

# 2) Run dev environment (interactive shell)
dev: build
	docker run -it --rm \
		-v $(PWD):/app \
		-v $(HOME)/.ssh:/root/.ssh:ro \
		-e HOME=/root \
		-w /app \
		-p 8501:8501 \
		$(IMAGE_NAME) \
		bash

# 3) Run tests (pytest) — uses docker on host, pytest directly in-container
test:
ifeq (, $(shell which docker))
	PYTHONPATH=/app/src pytest --maxfail=1 --disable-warnings -q
else
	docker run --rm \
		-v $(PWD):/app \
		-v $(HOME)/.ssh:/root/.ssh:ro \
		-e HOME=/root \
		-w /app \
		-e PYTHONPATH=/app/src \
		$(IMAGE_NAME) \
		pytest -vvv --maxfail=1 --disable-warnings
endif

live-test:
	docker run --rm \
		-v $(PWD):/app \
		-v $(HOME)/.ssh:/root/.ssh:ro \
		-e HOME=/root \
		-e PYTHONPATH=/app/src \
		-e VLF_HOST=100.76.133.15 \
		-e VLF_USER=User \
		-e VLF_KEY_PATH=/root/.ssh/id_ed25519 \
		-w /app \
		$(IMAGE_NAME) \
		pytest -vv tests/test_fetch_dates.py -s

# 4) Lint check (e.g. flake8)
check:
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		$(IMAGE_NAME) \
		flake8 .

# 5) Run the app (e.g. streamlit), with SSH keys available
show: build
	docker run -it --rm \
		-v $(PWD):/app \
		-v $(HOME)/.ssh:/root/.ssh:ro \
		-v ${SSH_AUTH_SOCK}:/ssh-agent \
		-e SSH_AUTH_SOCK=/ssh-agent \
		-e HOME=/root \
		-w /app \
		-p 8501:8501 \
		-e PYTHONPATH=/app/src \
		$(IMAGE_NAME) \
		streamlit run src/ui/main.py

# 6) Format & sort imports
fix-format:
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		$(IMAGE_NAME) \
		sh -c "black . && isort ."

# 7) Stop all running containers
stop:
	docker stop $$(docker ps -q)

# 8) Remove all stopped containers
clean:
	docker rm $$(docker ps -a -q)