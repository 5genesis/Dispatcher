FROM python:3.7.4-slim

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

#ENV INSTALL_PATH /OSM
#RUN mkdir -p $INSTALL_PATH

WORKDIR /validator

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /validator

EXPOSE 5100
CMD [ "python", "validator.py" ]

