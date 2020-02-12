FROM luigidifraia/dask-datacube:v1.1.0-alpha as BaseStage
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

COPY . /app/
WORKDIR /app/

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt