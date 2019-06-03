# ASKCOS Deployment - Containerized with Docker, deployed with docker-compose

### Prerequisites

 - If you're buidling the image from scratch, make sure git (and git lfs) is installed on your machine
 - Install Docker [OS specific instructions](https://docs.docker.com/install/)
 - Install docker-compose [installation instructions](https://docs.docker.com/compose/install/#install-compose)

### Upgrading from a previous version

#### Backing up user data

If you are upgrading the deployment from a previous version, you may want to retain user accounts and user-saved data. These are stored in an sqlite db at `askcos/db.sqlite3` and a user\_saves directory at `makeit/data/user_saves`, _in the running app container service_. The name of the running app service can be found using `docker-compose ps`; it should be called `deploy_app_1` Follow these steps to backup and restore user data:

__if the old version was < 0.2.3:__

```bash
$ docker cp deploy_app_1:/home/askcos/ASKCOS/askcos/db.sqlite3 .
$ docker cp deploy_app_1:/home/askcos/ASKCOS/makeit/data/user_saves .
# deploy new version
$ docker cp db.sqlite3 deploy_app_1:/usr/local/ASKCOS/askcos/db.sqlite3
$ docker cp user_saves deploy_app_1:/usr/local/ASKCOS/makeit/data/
```

__if the old version was >= 0.2.3:__

```bash
$ docker cp deploy_app_1:/usr/local/ASKCOS/askcos/db.sqlite3 .
$ docker cp deploy_app_1:/usr/local/ASKCOS/makeit/data/user_saves .
# deploy new version
$ docker cp db.sqlite3 deploy_app_1:/usr/local/ASKCOS/askcos/db.sqlite3
$ docker cp user_saves deploy_app_1:/usr/local/ASKCOS/makeit/data/
```

#### Updating static files

The static files (css/js) are stored in a volume, independent from the container services. When upgrading to a new version, it is important to ensure this volume gets recreated as well. The best way to do this is use `docker-compose down -v` (note the `-v` flag for volumes), followed by `docker-compose up -d`. docker-compose is intelligent enough to recreate container services with `up -d` when they have changed, but it is important to bring down the whole stack to make sure the volume gets recreated.

```bash
# only do this if you've already backed up user data!
$ docker-compose down -v
$ docker-compose up -d
```

However, if you are certain the celery worker images have not changed and would prefer to not bring these services down and then back up (to minimize application downtime), you can stop and remove the `app` and `nginx` services, delete the `deploy_staticdata` volume, then recreate the `app` and `nginx` services (which will recreate the volume with the correct static files) using the following:

```bash
# only do this if you've already backed up user data!
$ docker-compose stop app nginx
$ docker-compose rm app nginx
$ docker volume prune
$ docker-compose up -d app nginx
```

### Pulling the image from DockerHub

Pre-built images for versioned releases are available from [DockerHub](https://hub.docker.com/). You will need an DockerHub account, and you will need to be added to the private repository. Contact [mef231@mit.edu](mef231@mit.edu) with your username to be given access. If you pull the image from DockerHub, you can skip the (slow) build process below.

```bash
$ docker login # enter credentials
$ docker pull mefortunato/askcos # optionally supply :<version-number>
$ docker tag mefortunato/askcos askcos # docker-compose still looks for 'askcos' image
```

__If you pull from DockerHub, skip the build process below.__

### (Optional) Building the ASKCOS Image

The askcos image itself can be built using the Dockerfile in this repository `Make-It/Dockerfile`.

```bash
$ git clone https://github.com/connorcoley/Make-It  
$ cd Make-It/makeit/data  
$ git lfs pull  
$ cd ../../  
$ docker build -t askcos .
```

### Add customization

There are a few parts of the application that you can customize:
* Header sub-title next to ASKCOS (to designate this as a local deployment at your organization)
* Contact emails for centralized IT support

These are handled as environment variables that can change upon deployment (and are therefore not tied into the image directly). They can be found in `deploy/customization`. Please let us know what other degrees of customization you would like.

### Deploy with docker-compose

The `Make-It/deploy/docker-compose.yml` file contains the configuration to deploy the askcos stack with docker-compose. This requires that the askcos image is built (see previous step), and a few environment variables are set in the .env file. The default ENV values will work, but it is better to set `CURRENT_HOST` to the IP address of the machine you are deploying on, and to set the MongoDB credentials if you have access.

```bash
$ cd deploy  
$ docker-compose up -d
```

The services will start in a detached state. You can view logs with `docker-compose logs [-f]`.

To stop the containers use `docker-compose stop`. To restart the containers use `docker-compose start`. To completely delete the containers and volumes use `docker-compose down -v` (this deletes user database and saves; read section about backing up data first).

### Managing Django

If you'd like to manage the Django app (i.e. - run python manage.py ...), for example, to create an admin superuser, you can run commands in the _running_ app service (do this _after_ `docker-compose up`) as follows:

`docker-compose exec app bash -c "python /usr/local/ASKCOS/askcos/manage.py createsuperuser"`

In this case you'll be presented an interactive prompt to create a superuser with your desired credentials.

## Important Notes

#### First startup

The celery worker will take a few minutes to start up (possibly up to 5 minutes; it reads a lot of data into memory from disk). The web app itself will be ready before this, however upon the first get request (only the first for each process) a few files will be read from disk, so expect a 10-15 second delay.

#### Scaling workers

Only 1 worker per queue is deployed by default with limited concurrency. This is not ideal for many-user demand. You can easily scale the number of celery workers you'd like to use with `docker-compose up -d --scale tb_c_worker=N` where N is the number of workers you want, for example. The above note applies to each worker you start, however, and each worker will consume RAM.

## Future Improvements

 - Container orchestration with Kubernetes (will allow for distributed celery workers on multiple machines)