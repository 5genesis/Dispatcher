FROM python:3.7.4-slim

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

COPY clean_cache.py ./

CMD [ "python", "clean_cache.py" ]