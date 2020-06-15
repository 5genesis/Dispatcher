#FROM python:3.8-alpine
FROM python:3.7.4-slim

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

WORKDIR /auth
COPY requirements.txt ./

#RUN apk add --update --no-cache gcc musl-dev python-dev libffi-dev openssl-dev
RUN apt-get install -y gcc musl-dev python-dev libffi-dev libssl-dev


RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /auth

EXPOSE 2000
CMD [ "python", "auth.py" ]

