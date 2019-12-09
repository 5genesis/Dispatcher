#!/bin/bash

# Start the docker containers in the background

COMPOSE_HTTP_TIMEOUT=200 docker-compose -f docker-compose.yml up -d
