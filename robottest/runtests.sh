#!/bin/bash

docker exec -ti robottest service lighttpd start
docker exec -it robottest robot -d results testsuite/dispatcher_test.robot
