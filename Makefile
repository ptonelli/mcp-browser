PROJECT_NAME := mcp-browser
REGISTRY := docker.nautil.org

docker:
	docker build -t $(REGISTRY)/$(PROJECT_NAME) .

docker-nocache:
	docker build --no-cache -t $(REGISTRY)/$(PROJECT_NAME) .

push:
	$(eval VERSION = $(shell date +%Y%m%d%H%M))
	$(eval COMPLETE_NAME = $(REGISTRY)/$(PROJECT_NAME):$(VERSION))
	docker tag $(REGISTRY)/$(PROJECT_NAME) $(COMPLETE_NAME)
	docker push $(COMPLETE_NAME)

