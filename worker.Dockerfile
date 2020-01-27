FROM cubequery_base
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

CMD ["python", "-m", "celery", "worker", "-A", "cubequery.api_server.celery_app"]
