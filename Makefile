#!make
MAKEFLAGS += --silent
include .env
export $(shell sed 's/=.*//' .env)

install_plugin:
	(cd ./collector-plugin && python ../octoprint/run dev plugin:install)

serve:
	(cd ./octoprint && python run --config ../.octoprint/config.yaml --basedir ../.octoprint)

install:
	mkdir -p ./.octoprint
	cp octoprint-config.yaml ./.octoprint/config.yaml
	(cd ./octoprint && pip install -e .[develop,plugins])
	
	(cd ./mjpeg-streamer/mjpg-streamer-experimental && make)
	
	wget https://dl.min.io/server/minio/release/linux-amd64/minio --directory-prefix=.minio
	chmod +x ./.minio/minio

	(cd ./collector-api && npm install)

stream:
	(cd ./mjpeg-streamer/mjpg-streamer-experimental && sh start.sh)

minio:
	./.minio/minio server --config-dir ./minio/config ./.minio/data

dev: install_plugin
	make -j stream serve minio

.PHONY: dev
.DEFAULT_GOAL := dev

.PHONY: install_plugin
.PHONY: serve
.PHONY: install
.PHONY: stream
.PHONY: minio