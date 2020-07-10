#From robot:melian
From javimelian/robottesting:latest

ENV ROBOT_WORK_DIR /robotTesting
ENV PACKAGES_DIR /robotTesting/packages
ENV TEST_IMAGE test_image.img

#5MB
ARG IMAGE_SIZE=5000

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

WORKDIR ${ROBOT_WORK_DIR}

COPY . ${ROBOT_WORK_DIR}

# Creation of a fake image file only for testing purposes
RUN dd if=/dev/urandom of=${PACKAGES_DIR}/${TEST_IMAGE} bs=${IMAGE_SIZE} count=1024

# Port for the web reports
EXPOSE 80

# Restart the web service for the logs
#ENTRYPOINT sed 's@\/home@'"$ROBOT_RESULTS_DIR"'@g' /etc/lighttpd/lighttpd.conf > /etc/lighttpd/lighttpd.conf2 && mv /etc/lighttpd/lighttpd.conf2 /etc/lighttpd/lighttpd.conf && service lighttpd restart && /bin/bash
ENTRYPOINT ["sh", "./start.sh"]
# Execute all robot tests
#CMD ["runtests.sh"]
