
docker build -f server.Dockerfile -t cubequery_server:latest .
docker build -f worker.Dockerfile -t cubequery_worker:latest .