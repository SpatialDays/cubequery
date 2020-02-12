# CubeQuery

This is a tool to provide an api to produce data products from an open data cube. 

## Building and deployment

This project is not designed to be built and run stand alone. You are expected to use the containers
that this produces as base layers for your own containers, with your workflows and processes embedded
inside. See the [cubequery-deployment](https://github.com/SatelliteApplicationsCatapult/cubequery-deployment)  project
for an example of how this should work.

Most of the build for this project works through the `Makefile` 

Run `make docker` to build the base containers to work on top of.

## Architecture
 
 CubeQuery is made up of three components. 
 
 1) The server - This [flask](https://flask.palletsprojects.com/en/1.1.x/) app hosts the rest end points to create jobs, 
 find out what jobs are available and see what jobs are running.
 1) [Redis](https://redis.io/) - This hosts the task queue. Jobs are submitted from the server and then worked on by the 
 workers.
 1) The workers - This is a [celery](http://www.celeryproject.org/) worker that executes jobs from the queue.
 
 The server and the workers will be based on the containers built from here. The redis deployment can use a standard
 redis container.
 
 When deploying this the server and the workers must have the same set of processes accessible on both containers. 
 When adding a process: recreate the workers first, and then the server.
 When removing a process: recreate the server first, then the workers. 
 This should mean that you don't end up with tasks being submitted that the workers do not know how to handle.
 
 There can be many workers as you need to keep up with load. We have not tested dynamic creation and removal of workers
 yet.
 