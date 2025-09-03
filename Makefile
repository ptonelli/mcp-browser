# Makefile

PROJECT   := mcp-browser
REGISTRY  ?= registry.example.com   # your private registry hostname
NAMESPACE ?=                        # optional; leave empty if not used
CONTEXT   ?= .

# Resolve image name with optional namespace
IMAGE := $(REGISTRY)$(if $(strip $(NAMESPACE)),/$(strip $(NAMESPACE)))/$(PROJECT)

.PHONY: docker dockerx docker-nocache push

docker:
	docker build -t $(IMAGE):latest $(CONTEXT)

dockerx:
	VERSION=$$(date +%Y%m%d%H%M); \
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(IMAGE):$$VERSION -t $(IMAGE):latest \
		--push $(CONTEXT)

docker-nocache:
	docker build --no-cache -t $(IMAGE):latest $(CONTEXT)

push:
	VERSION=$$(date +%Y%m%d%H%M); \
	docker tag $(IMAGE):latest $(IMAGE):$$VERSION; \
	docker push $(IMAGE):$$VERSION; \
	docker push $(IMAGE):latest
