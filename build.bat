
docker build -f base.Dockerfile -t cubequery_base .
docker build -f server.Dockerfile -t cubequery_server .
docker build -f worker.Dockerfile -t cubequery_worker .