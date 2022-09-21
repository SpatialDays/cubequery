FROM satapps/dask-datacube:v3.2.20
LABEL maintainer="Emily Selwood <emily.selwood@sa.catapult.org.uk>"

COPY . /app/
WORKDIR /app/

RUN apt-get --allow-releaseinfo-change update \
    && apt-get install -yq --no-install-recommends \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --extra-index-url="https://packages.dea.ga.gov.au" -r requirements.txt

RUN mamba install --yes \
    -c conda-forge \
    geopandas \
    hdmedians \
    && conda clean -tipsy \
    && find /opt/conda/ -type f,l -name '*.a' -delete \
    && find /opt/conda/ -type f,l -name '*.pyc' -delete \
    && find /opt/conda/ -type f,l -name '*.js.map' -delete \
    && rm -rf /opt/conda/pkgs

CMD ["python", "-m", "cubequery.notebook_validation"]