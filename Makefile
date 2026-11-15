IMAGE     := studytask-manager
CONTAINER := studytask-manager
PORT      ?= 8000

# Extra flags for build/test, e.g. `make build NET=--network=host`
NET ?=

.PHONY: build run stop logs test clean

build:
	docker build $(NET) -t $(IMAGE) .

run:
	docker run -d --name $(CONTAINER) -p $(PORT):8000 -v studytask-data:/data $(IMAGE)
	@echo "App running at http://localhost:$(PORT)"

stop:
	-docker stop $(CONTAINER)
	-docker rm $(CONTAINER)

logs:
	docker logs -f $(CONTAINER)

test:
	docker run --rm $(NET) -v "$(CURDIR)":/work -w /work python:3.12-slim \
		sh -c "pip install -q --root-user-action=ignore -r requirements-dev.txt && pytest -q -p no:cacheprovider"

clean: stop
	-docker rmi $(IMAGE)
	-docker volume rm studytask-data
