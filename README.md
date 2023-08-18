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
