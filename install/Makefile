TAG := version-1.5
IMAGE := ethsrilab/zkay-prerequisites
FULL_IMAGE := ethsrilab/zkay
FULL_CONTAINER := zkay-container

# build the prerequisites docker image
.PHONY: image
image:
	docker build -t $(IMAGE):$(TAG) .
	docker history --no-trunc $(IMAGE):$(TAG)

.PHONY: login
login:
	docker login

.PHONY: deploy
deploy: login image
	docker push $(IMAGE):$(TAG)

# build the full docker image
.PHONY: full-image
full-image:
	docker build -t $(FULL_IMAGE):$(TAG) --build-arg INSTALL_ZKAY=1 .
	docker history --no-trunc $(FULL_IMAGE):$(TAG)

# launch a docker container using the image, which will provide a shell in the container
.PHONY: run
run: full-image
	docker run -it --rm --name $(FULL_CONTAINER) $(FULL_IMAGE):$(TAG)
