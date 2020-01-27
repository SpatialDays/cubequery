FROM python:3.7 as BaseStage
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

WORKDIR /app/

ADD ./ /app/

RUN apt-get update \
    && apt-get install -y redis \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && apt-get clean