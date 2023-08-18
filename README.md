https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/

This is a step-by-step tutorial that details how to configure Django to run on Docker with Postgres. For production environments, we'll add on Nginx and Gunicorn. We'll also take a look at how to serve Django static and media files via Nginx.

*Dependencies:*

1. Django v4.2.3
2. Docker v24.0.2
3. Python v3.11.4

Django on Docker Series:

| 1. Dockerizing Django with Postgres, Gunicorn, and Nginx (this tutorial!)

| 2. Securing a Containerized Django Application with Let's Encrypt

| 3. Deploying Django to AWS with Docker and Let's Encrypt

# Project Setup

Create a new project directory along with a new Django project:
<pre>
$ mkdir django-on-docker && cd django-on-docker
$ mkdir app && cd app
$ python3.11 -m venv env
$ source env/bin/activate
(env)$

(env)$ pip install django==4.2.3
(env)$ django-admin startproject hello_django .
(env)$ python manage.py migrate
(env)$ python manage.py runserver</pre>

Navigate to http://localhost:8000/ to view the Django welcome screen. Kill the server once done. Then, exit from and remove the virtual environment. We now have a simple Django project to work with.

Create a *requirements.txt* file in the "app" directory and add Django as a dependency:
<pre>Django==4.2.3</pre>
Since we'll be moving to Postgres, go ahead and remove the db.sqlite3 file from the "app" directory.
Your project directory should look like:
<pre>
├── app
│   ├── db.sqlite3
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── entrypoint.prod.sh
│   ├── entrypoint.sh
│   ├── env
│   │   ├── bin
│   │   ├── include
│   │   ├── lib
│   │   ├── lib64 -> lib
│   │   └── pyvenv.cfg
│   ├── hello_django
│   │   ├── asgi.py
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── manage.py
│   ├── mediafiles
│   │   └── phis_v1 - 2023-08-16T115906_063.xml
│   ├── requirements.txt
│   └── upload
│       ├── admin.py
│       ├── apps.py
│       ├── __init__.py
│       ├── migrations
│       ├── models.py
│       ├── templates
│       ├── tests.py
│       ├── upload.html
│       └── views.py
├── docker-compose.prod.yml
├── docker-compose.yml
└── nginx
    ├── Dockerfile
    └── nginx.conf

</pre>

# Docker
Install Docker, if you don't already have it, then add a Dockerfile to the "app" directory:

<pre>
  # pull official base image
FROM python:3.11.4-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .
</pre>

So, we started with a ``slim-buster``-based Docker image for Python 3.11.4. We then set a working directory along with two environment variables:

1. ``PYTHONDONTWRITEBYTECODE``: Prevents Python from writing pyc files to disc (equivalent to ``python -B`` option)
2. ``PYTHONUNBUFFERED``: Prevents Python from buffering stdout and stderr (equivalent to ``python -u`` option)

Finally, we updated Pip, copied over the requirements.txt file, installed the dependencies, and copied over the Django project itself.

| Review [Docker Best Practices for Python Developers](https://testdriven.io/blog/docker-best-practices/) for more on structuring Dockerfiles as well as some best practices for configuring Docker for Python-based development.

Next, add a *docker-compose.yml* file to the project root:

<pre>
version: '3.8'

services:
  web:
    build: ./app
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./app/:/usr/src/app/
    ports:
      - 8000:8000
    env_file:
      - ./.env.dev
</pre>

| Review the [Compose file reference](https://docs.docker.com/compose/compose-file/) for info on how this file works.

Update the `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` variables in *settings.py*:

<pre>
SECRET_KEY = os.environ.get("SECRET_KEY")

DEBUG = bool(os.environ.get("DEBUG", default=0))

# 'DJANGO_ALLOWED_HOSTS' should be a single string of hosts with a space between each.
# For example: 'DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]'
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")
</pre>

Make sure to add the import to the top:

<pre>import os</pre>

Then, create a *.env.dev* file in the project root to store environment variables for development:

<pre>
DEBUG=1
SECRET_KEY=foo
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
</pre>

Build the image:

<pre>
  $ docker-compose build
</pre>

Once the image is built, run the container:

<pre>$ docker-compose up -d</pre>

Navigate to http://localhost:8000/ to again view the welcome screen.

| Check for errors in the logs if this doesn't work `via docker-compose logs -f`.

# Postgres
To configure Postgres, we'll need to add a new service to the *docker-compose.yml* file, update the Django settings, and install [Psycopg2](https://www.psycopg.org/).

First, add a new service called `db` to *docker-compose.yml*:

<pre>
version: '3.8'

services:
  web:
    build: ./app
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./app/:/usr/src/app/
    ports:
      - 8000:8000
    env_file:
      - ./.env.dev
    depends_on:
      - db
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=hello_django
      - POSTGRES_PASSWORD=hello_django
      - POSTGRES_DB=hello_django_dev

volumes:
  postgres_data:
</pre>
To persist the data beyond the life of the container we configured a volume. This config will bind `postgres_data` to the "/var/lib/postgresql/data/" directory in the container.

We also added an environment key to define a name for the default database and set a username and password.

| Review the "Environment Variables" section of the [Postgres Docker Hub](https://hub.docker.com/_/postgres) page for more info.

We'll need some new environment variables for the `web` service as well, so update *.env.dev* like so:
<pre>
DEBUG=1
SECRET_KEY=foo
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=hello_django_dev
SQL_USER=hello_django
SQL_PASSWORD=hello_django
SQL_HOST=db
SQL_PORT=5432
</pre>

Update the `DATABASES` dict in *settings.py*:
<pre>
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}
</pre>
Here, the database is configured based on the environment variables that we just defined. Take note of the default values.

Add Psycopg2 to *requirements.txt*:
<pre>Django==4.2.3
psycopg2-binary==2.9.6</pre>
Build the new image and spin up the two containers:
<pre>$ docker-compose up -d --build</pre>
Run the migrations:
<pre>$ docker-compose exec web python manage.py migrate --noinput</pre>

| Get the following error?
<pre>django.db.utils.OperationalError: FATAL:  database "hello_django_dev" does not exist</pre>
| Run `docker-compose down -v` to remove the volumes along with the containers. Then, re-build the images, run the containers, and apply the migrations.
You can check that the volume was created as well by running:
<pre>$ docker volume inspect django-on-docker_postgres_data</pre>
You should see something similar to:
<pre>[
    {
        "CreatedAt": "2023-07-20T14:15:27Z",
        "Driver": "local",
        "Labels": {
            "com.docker.compose.project": "django-on-docker",
            "com.docker.compose.version": "2.19.1",
            "com.docker.compose.volume": "postgres_data"
        },
        "Mountpoint": "/var/lib/docker/volumes/django-on-docker_postgres_data/_data",
        "Name": "django-on-docker_postgres_data",
        "Options": null,
        "Scope": "local"
    }
]</pre>

Next, add an *entrypoint.sh* file to the "app" directory to verify that Postgres is healthy *before* applying the migrations and running the Django development server:
<pre>#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py flush --no-input
python manage.py migrate

exec "$@"</pre>
Update the file permissions locally:
<pre>$ chmod +x app/entrypoint.sh</pre>
Then, update the Dockerfile to copy over the *entrypoint.s*h file and run it as the Docker [entrypoint](https://docs.docker.com/engine/reference/builder/#entrypoint) command:
<pre># pull official base image
FROM python:3.11.4-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && apt-get install -y netcat

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]</pre>
Add the `DATABASE` environment variable to *.env.dev*:
<pre>DEBUG=1
SECRET_KEY=foo
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=hello_django_dev
SQL_USER=hello_django
SQL_PASSWORD=hello_django
SQL_HOST=db
SQL_PORT=5432
DATABASE=postgres</pre>

Test it out again:
1. Re-build the images
2. Run the containers
3. Try http://localhost:8000/
## Notes
First, despite adding Postgres, we can still create an independent Docker image for Django as long as the `DATABASE` environment variable is not set to `postgres`. To test, build a new image and then run a new container:
<pre>$ docker build -f ./app/Dockerfile -t hello_django:latest ./app
$ docker run -d \
    -p 8006:8000 \
    -e "SECRET_KEY=please_change_me" -e "DEBUG=1" -e "DJANGO_ALLOWED_HOSTS=*" \
    hello_django python /usr/src/app/manage.py runserver 0.0.0.0:8000</pre>
    
You should be able to view the welcome page at http://localhost:8006

Second, you may want to comment out the database flush and migrate commands in the entrypoint.sh script so they don't run on every container start or re-start:
<pre>#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# python manage.py flush --no-input
# python manage.py migrate

exec "$@"</pre>
Instead, you can run them manually, after the containers spin up, like so:
<pre>$ docker-compose exec web python manage.py flush --no-input
$ docker-compose exec web python manage.py migrate</pre>
