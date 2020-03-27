FROM python:3.7.4-alpine

WORKDIR /auth
COPY requirements.txt ./

RUN apk add gcc musl-dev python-dev libffi-dev openssl-dev

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /auth

EXPOSE 2000
CMD [ "python", "auth.py" ]

