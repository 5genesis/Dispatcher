#!/bin/bash

docker rm -f robot && \
docker build -t robottest . && \ 
docker run -dit -p 8002:80 --env-file environment.rc --name robot robottest:latest

