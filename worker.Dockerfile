FROM cubequery_base
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

RUN groupadd -g 999 celery && \
    useradd -r -u 999 -g celery celery

RUN mkdir /cubequery-repo && chown -R celery:celery /cubequery-repo && chmod 777 -R /cubequery-repo
USER celery:celery

CMD ["python", "-m", "celery", "worker", "-E", "-A", "cubequery.api_server.celery_app", "--loglevel", "DEBUG"]
