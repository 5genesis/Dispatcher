FROM python:3.7.4-slim

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev openssh-client sshpass --no-install-recommends

#ENV INSTALL_PATH /OSM
#RUN mkdir -p $INSTALL_PATH

WORKDIR /mano

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /mano

EXPOSE 5101
CMD [ "python", "mano.py" ]
