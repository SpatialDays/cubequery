FROM python:3.7 AS BaseStage
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

WORKDIR /app/

ADD ./ /app/

RUN apt-get update \
    && apt-get install -y redis \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && apt-get clean


FROM BaseStage AS Worker
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

CMD ["python", "-m", "celery", "worker", "-A", "cubequery.api_server.celery_app"]

FROM BaseStage AS Server
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

CMD ["python", "cubequery/api_server.py"]