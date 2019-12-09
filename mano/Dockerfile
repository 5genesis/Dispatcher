FROM python:3.7.4-slim

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

#ENV INSTALL_PATH /OSM
#RUN mkdir -p $INSTALL_PATH

WORKDIR /MANO

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY MANO /MANO

EXPOSE 5001
CMD [ "python", "app.py" ]
