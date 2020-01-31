FROM python:3.8 as BaseStage
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

COPY . /app/
WORKDIR /app/

RUN apt-get update \
    && apt-get install -y redis \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean