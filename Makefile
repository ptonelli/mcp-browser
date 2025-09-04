# Makefile

PROJECT   := mcp-browser
CONTAINER_REGISTRY  ?= registry.example.com   # your private registry hostname
NAMESPACE ?=                        # optional; leave empty if your registry doesn't require a namespace
CONTEXT   ?= .

# Timestamp used for tags (computed once per make invocation)
VERSION := $(shell date +%Y%m%d%H%M)

# Resolve image name with optional namespace
IMAGE := $(CONTAINER_REGISTRY)$(if $(NAMESPACE),/$(NAMESPACE))/$(PROJECT)

.PHONY: docker dockerx docker-nocache push

docker:
	docker build -t $(IMAGE):latest $(CONTEXT)

dockerx:
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(IMAGE):$(VERSION) -t $(IMAGE):latest \
		--push $(CONTEXT)

docker-nocache:
	docker build --no-cache -t $(IMAGE):latest $(CONTEXT)

push:
	docker tag $(IMAGE):latest $(IMAGE):$(VERSION)
	docker push $(IMAGE):$(VERSION)
	docker push $(IMAGE):latest
