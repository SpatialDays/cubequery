FROM cubequery_base
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

CMD ["python", "-m", "cubequery.api_server"]