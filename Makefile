# Makefile

# Image name for the dev environment
IMAGE_NAME = cassandra-dev

# Default Docker build context is the .devcontainer folder
DOCKERFILE = .devcontainer/Dockerfile

# 1) Build the dev image
build:
	docker build -t $(IMAGE_NAME) -f $(DOCKERFILE) .

# 2) Run dev environment (interactive shell) 
#    mounting current dir for live editing
dev: build
	docker run -it --rm \
		-v $(PWD):/app \
		-w /app \
		-p 8501:8501 \
		$(IMAGE_NAME) \
		bash

# 3) Run tests (e.g. pytest)
test:
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		-e PYTHONPATH=/app/src \
		$(IMAGE_NAME) \
		pytest --maxfail=1 --disable-warnings -q

# 4) Lint check (e.g. flake8)
check:
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		$(IMAGE_NAME) \
		flake8 .

# 5) Run the app (e.g. streamlit)
show: build
	docker run -it --rm \
		-v $(PWD):/app \
		-w /app \
		-p 8501:8501 \
		-e PYTHONPATH=/app/src \
		$(IMAGE_NAME) \
		streamlit run src/UI/viewer.py

# 6) Clean up dangling images
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