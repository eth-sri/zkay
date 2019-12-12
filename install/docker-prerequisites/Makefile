# all commands involving docker use sudo, which is typically required to use docker commands

IMAGE := ethsrilab/zkay-prerequisites
TAG := version-1.2
CONTAINER := zkay-prerequisites-container

# build the docker image
.PHONY: image
image:
	sudo docker build -t $(IMAGE):$(TAG) .
	sudo docker history --no-trunc $(IMAGE):$(TAG)

# launch a docker container using the image, which will provide a shell in the container
.PHONY: run
run: image
	sudo docker run -it --rm --name $(CONTAINER) $(IMAGE):$(TAG)

.PHONY: login
login:
	sudo docker login

.PHONY: deploy
deploy: login image
	sudo docker push $(IMAGE):$(TAG)
