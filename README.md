# CubeQuery

This is a tool to provide an api to produce on demand data products from an open data cube. This system is made up of
two docker containers, as server and one or more workers. Each will fetch the potential processes from a GitHub repo 
defined in the configuration.

## Building and deployment

This project will automatically publish to docker hub on pushes to master.

The containers will need to be configured. See [config.cfg](config.cfg) All parameters in there can be adjusted with environment
variables upper case and with the section name prepended. E.G `APP_SECRET_KEY`

You will need to set `GIT_URL` at the very least to point to your repo of notebooks. 
See [NOTEBOOK_DETAILS.md](NOTEBOOK_DETAILS.md) for more information about the process notebooks.

## Architecture
 
 CubeQuery is made up of three components. 
 
 1) The server - This [flask](https://flask.palletsprojects.com/en/1.1.x/) app hosts the rest end points to create jobs, 
 find out what jobs are available and see what jobs are running.
 1) [Redis](https://redis.io/) - This hosts the task queue. Jobs are submitted from the server and then worked on by the 
 workers.
 1) The workers - This is a [celery](http://www.celeryproject.org/) worker that executes jobs from the queue.
 
 The server and the workers will be based on the containers built from here. The redis deployment can use a standard
 redis container. The processing code will be pulled from the configured github repo on start up.
 
 There can be many workers as you need to keep up with load. We have not tested dynamic creation and removal of workers
 yet.
 