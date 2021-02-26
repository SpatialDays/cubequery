FROM cubequery_base
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

RUN groupadd -g 999 celery && \
    useradd -r -u 999 -g celery celery
USER celery:celery

CMD ["python", "-m", "celery", "worker", "-E", "-A", "cubequery.api_server.celery_app", "--loglevel", "DEBUG"]