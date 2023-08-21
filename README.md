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

# Gunicorn

Moving along, for production environments, let's add [Gunicorn](https://gunicorn.org/), a production-grade WSGI server, to the requirements file:
<pre>Django==4.2.3
gunicorn==21.2.0
psycopg2-binary==2.9.6</pre>
| Curious about WSGI and Gunicorn? Review the [WSGI](https://testdriven.io/courses/python-web-framework/wsgi/) chapter from the [Building Your Own Python Web Framework](https://testdriven.io/courses/python-web-framework/) course.

Since we still want to use Django's built-in server in development, create a new compose file called *docker-compose.prod.yml* for production:

<pre>version: '3.8'

services:
  web:
    build: ./app
    command: gunicorn hello_django.wsgi:application --bind 0.0.0.0:8000
    ports:
      - 8000:8000
    env_file:
      - ./.env.prod
    depends_on:
      - db
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - ./.env.prod.db

volumes:
  postgres_data:</pre>
| If you have multiple environments, you may want to look at using a [docker-compose.override.yml](https://docs.docker.com/compose/extends/) configuration file. With this approach, you'd add your base config to a *docker-compose.yml* file and then use a *ocker-compose.override.yml* file to override those config settings based on the environment.

Take note of the default `command`. We're running Gunicorn rather than the Django development server. We also removed the volume from the `web` service since we don't need it in production. Finally, we're using [separate environment variable files](https://docs.docker.com/compose/env-file/) to define environment variables for both services that will be passed to the container at runtime.

*.env.prod:*
<pre>POSTGRES_USER=hello_django
POSTGRES_PASSWORD=hello_django
POSTGRES_DB=hello_django_prod</pre>

Add the two files to the project root. You'll probably want to keep them out of version control, so add them to a *.gitignore* file.

Bring [down](https://docs.docker.com/compose/reference/down/) the development containers (and the associated volumes with the `-v` flag):
<pre>$ docker-compose down -v</pre>
Then, build the production images and spin up the containers:
<pre>$ docker-compose -f docker-compose.prod.yml up -d --build</pre>
Verify that the `hello_django_prod` database was created along with the default Django tables. Test out the admin page at http://localhost:8000/admin. The static files are not being loaded anymore. This is expected since Debug mode is off. We'll fix this shortly.

| Again, if the container fails to start, check for errors in the logs via `docker-compose -f docker-compose.prod.yml logs -f`.
# Production Dockerfile
Did you notice that we're still running the database [flush](https://docs.djangoproject.com/en/4.2/ref/django-admin/#flush) (which clears out the database) and migrate commands every time the container is run? This is fine in development, but let's create a new entrypoint file for production.
*entrypoint.prod.sh*:
<pre>#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

exec "$@</pre>
Update the file permissions locally:
<pre>$ chmod +x app/entrypoint.prod.sh</pre>
To use this file, create a new Dockerfile called Dockerfile.prod for use with production builds:
<pre>###########
# BUILDER #
###########

# pull official base image
FROM python:3.11.4-slim-buster as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

# lint
RUN pip install --upgrade pip
RUN pip install flake8==6.0.0
COPY . /usr/src/app/
RUN flake8 --ignore=E501,F401 .

# install python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


#########
# FINAL #
#########

# pull official base image
FROM python:3.11.4-slim-buster

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends netcat
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

# copy entrypoint.prod.sh
COPY ./entrypoint.prod.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/entrypoint.prod.sh
RUN chmod +x  $APP_HOME/entrypoint.prod.sh

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

# run entrypoint.prod.sh
ENTRYPOINT ["/home/app/web/entrypoint.prod.sh"]</pre>
Here, we used a Docker [multi-stage build](https://docs.docker.com/develop/develop-images/multistage-build/) to reduce the final image size. Essentially, `builder` is a temporary image that's used for building the Python wheels. The wheels are then copied over to the final production image and the `builder` image is discarded.

| You could take the [multi-stage build approach](https://stackoverflow.com/a/53101932/1799408) a step further and use a single Dockerfile instead of creating two Dockerfiles. Think of the pros and cons of using this 
approach over two different files.

Did you notice that we created a non-root user? By default, Docker runs container processes as root inside of a container. This is a bad practice since attackers can gain root access to the Docker host if they manage to break out of the container. If you're root in the container, you'll be root on the host.

Update the `web` service within the *docker-compose.prod.yml* file to build with *Dockerfile.prod*:
<pre>web:
  build:
    context: ./app
    dockerfile: Dockerfile.prod
  command: gunicorn hello_django.wsgi:application --bind 0.0.0.0:8000
  ports:
    - 8000:8000
  env_file:
    - ./.env.prod
  depends_on:
    - db</pre>

Try it out:
<pre>$ docker-compose -f docker-compose.prod.yml down -v
$ docker-compose -f docker-compose.prod.yml up -d --build
$ docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput</pre>

# Nginx

Next, let's add Nginx into the mix to act as a [reverse proxy](https://www.nginx.com/resources/glossary/reverse-proxy-server/) for Gunicorn to handle client requests as well as serve up static files.

Add the service to *docker-compose.prod.yml*:
<pre>nginx:
  build: ./nginx
  ports:
    - 1337:80
  depends_on:
    - web</pre>
Then, in the local project root, create the following files and folders:
<pre>└── nginx
    ├── Dockerfile
    └── nginx.conf</pre>
*Dockerfile*:
<pre>FROM nginx:1.25

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d</pre>
*nginx.conf:*
<pre>upstream hello_django {
    server web:8000;
}

server {

    listen 80;

    location / {
        proxy_pass http://hello_django;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }

}</pre>

| Review [Using NGINX and NGINX Plus as an Application Gateway with uWSGI and Django](https://docs.nginx.com/nginx/admin-guide/web-server/app-gateway-uwsgi-django/) for more info on configuring Nginx to work with Django.

Then, update the `web` service, in *docker-compose.prod.yml*, replacing `ports` with `expose`:
<pre>web:
  build:
    context: ./app
    dockerfile: Dockerfile.prod
  command: gunicorn hello_django.wsgi:application --bind 0.0.0.0:8000
  expose:
    - 8000
  env_file:
    - ./.env.prod
  depends_on:
    - db</pre>
Now, port 8000 is only exposed internally, to other Docker services. The port will no longer be published to the host machine.

For more on ports vs expose, review [this](https://stackoverflow.com/questions/40801772/what-is-the-difference-between-docker-compose-ports-vs-expose) Stack Overflow question.

Ensure the app is up and running at http://localhost:1337.

Your project structure should now look like:

Test it out again.

<pre>$ docker-compose -f docker-compose.prod.yml down -v
$ docker-compose -f docker-compose.prod.yml up -d --build
$ docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput</pre>

Ensure the app is up and running at http://localhost:1337.

Bring the containers down once done:

<pre>$ docker-compose -f docker-compose.prod.yml down -v</pre>

Since Gunicorn is an application server, it will not serve up static files. So, how should both static and media files be handled in this particular configuration?

# Static Files

Update *settings.py*:
<pre>STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"</pre>

**Development**

Now, any request to `http://localhost:8000/static/*` will be served from the "staticfiles" directory.

**Production**

For production, add a volume to the `web` and `nginx` services in docker-compose.prod.yml so that each container will share a directory named "staticfiles":
<pre>version: '3.8'

services:
  web:
    build:
      context: ./app
      dockerfile: Dockerfile.prod
    command: gunicorn hello_django.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - static_volume:/home/app/web/staticfiles
    expose:
      - 8000
    env_file:
      - ./.env.prod
    depends_on:
      - db
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - ./.env.prod.db
  nginx:
    build: ./nginx
    volumes:
      - static_volume:/home/app/web/staticfiles
    ports:
      - 1337:80
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:</pre>

  We need to also create the "/home/app/web/staticfiles" folder in *Dockerfile.prod*:
  <pre>...

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

...</pre>

Why is this necessary?

Docker Compose normally mounts named volumes as root. And since we're using a non-root user, we'll get a permission denied error when the `collectstatic` command is run if the directory does not already exist

To get around this, you can either:

Create the folder in the Dockerfile ([source](https://github.com/docker/compose/issues/3270#issuecomment-206214034))
Change the permissions of the directory after it's mounted ([source](https://stackoverflow.com/a/40510068/1799408))

We used the former.

<pre>upstream hello_django {
    server web:8000;
}

server {

    listen 80;

    location / {
        proxy_pass http://hello_django;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/app/web/staticfiles/;
    }

}</pre>
Spin down the development containers:
<pre>$ docker-compose down -v</pre>
Test:
<pre>$ docker-compose -f docker-compose.prod.yml up -d --build
$ docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
$ docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear</pre>
Next, update the Nginx configuration to route static file requests to the "staticfiles" folder:

Again, requests to `http://localhost:1337/static/*` will be served from the "staticfiles" directory.

Navigate to http://localhost:1337/admin and ensure the static assets load correctly.

You can also verify in the logs -- via `docker-compose -f docker-compose.prod.yml logs -f` -- that requests to the static files are served up successfully via Nginx:

<pre>nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /admin/ HTTP/1.1" 302 0 "-" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"
nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /admin/login/?next=/admin/ HTTP/1.1" 200 2214 "-" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"
nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /static/admin/css/base.css HTTP/1.1" 304 0 "http://localhost:1337/admin/login/?next=/admin/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"
nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /static/admin/css/nav_sidebar.css HTTP/1.1" 304 0 "http://localhost:1337/admin/login/?next=/admin/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"
nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /static/admin/css/responsive.css HTTP/1.1" 304 0 "http://localhost:1337/admin/login/?next=/admin/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"
nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /static/admin/css/login.css HTTP/1.1" 304 0 "http://localhost:1337/admin/login/?next=/admin/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"
nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /static/admin/js/nav_sidebar.js HTTP/1.1" 304 0 "http://localhost:1337/admin/login/?next=/admin/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"
nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /static/admin/css/fonts.css HTTP/1.1" 304 0 "http://localhost:1337/static/admin/css/base.css" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"
nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /static/admin/fonts/Roboto-Regular-webfont.woff HTTP/1.1" 304 0 "http://localhost:1337/static/admin/css/fonts.css" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"
nginx_1  | 192.168.144.1 - - [23/Aug/2021:20:11:00 +0000] "GET /static/admin/fonts/Roboto-Light-webfont.woff HTTP/1.1" 304 0 "http://localhost:1337/static/admin/css/fonts.css" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" "-"</pre>

Bring the containers once done:

<pre>docker-compose -f docker-compose.prod.yml down -v</pre>

# Media Files
To test out the handling of media files, start by creating a new Django app:

<pre>$ docker-compose up -d --build
$ docker-compose exec web python manage.py startapp upload</pre>

Add the new app to the `INSTALLED_APPS` list in *settings.py*:

<pre>INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "upload",
]</pre>

*app/upload/views.py*:

<pre>from django.shortcuts import render
from django.core.files.storage import FileSystemStorage


def image_upload(request):
    if request.method == "POST" and request.FILES["image_file"]:
        image_file = request.FILES["image_file"]
        fs = FileSystemStorage()
        filename = fs.save(image_file.name, image_file)
        image_url = fs.url(filename)
        print(image_url)
        return render(request, "upload.html", {
            "image_url": image_url
        })
    return render(request, "upload.html")</pre>

    Add a "templates", directory to the "app/upload" directory, and then add a new template called *upload.html*:

<pre>{% block content %}

  <form action="{% url "upload" %}" method="post" enctype="multipart/form-data">
    {% csrf_token %}
    <input type="file" name="image_file">
    <input type="submit" value="submit" />
  </form>

  {% if image_url %}
    <p>File uploaded at: <a href="{{ image_url }}">{{ image_url }}</a></p>
  {% endif %}

{% endblock %}</pre>

*app/hello_django/urls.py*:
<pre>from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from upload.views import image_upload

urlpatterns = [
    path("", image_upload, name="upload"),
    path("admin/", admin.site.urls),
]

if bool(settings.DEBUG):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)</pre>
*app/hello_django/settings.py*:

<pre>MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"</pre>

**Development**

Test:

<pre>$ docker-compose up -d --build</pre>

You should be able to upload an image at http://localhost:8000/, and then view the image at http://localhost:8000/media/IMAGE_FILE_NAME.

**Production**

For production, add another volume to the `web` and `nginx` services:

<pre>version: '3.8'

services:
  web:
    build:
      context: ./app
      dockerfile: Dockerfile.prod
    command: gunicorn hello_django.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - static_volume:/home/app/web/staticfiles
      - media_volume:/home/app/web/mediafiles
    expose:
      - 8000
    env_file:
      - ./.env.prod
    depends_on:
      - db
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - ./.env.prod.db
  nginx:
    build: ./nginx
    volumes:
      - static_volume:/home/app/web/staticfiles
      - media_volume:/home/app/web/mediafiles
    ports:
      - 1337:80
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:</pre>

Create the "/home/app/web/mediafiles" folder in `Dockerfile.prod`:

<pre>...

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
RUN mkdir $APP_HOME/mediafiles
WORKDIR $APP_HOME

...</pre>

Update the Nginx config again:

<pre>upstream hello_django {
    server web:8000;
}

server {

    listen 80;

    location / {
        proxy_pass http://hello_django;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/app/web/staticfiles/;
    }

    location /media/ {
        alias /home/app/web/mediafiles/;
    }

}</pre>

Add the following to *settings.py*:

<pre>CSRF_TRUSTED_ORIGINS = ["http://localhost:1337"]</pre>

Re-build:

<pre>$ docker-compose down -v

$ docker-compose -f docker-compose.prod.yml up -d --build
$ docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput
$ docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear</pre>

Test it out one final time:

1. Upload an image at http://localhost:1337/.
2. Then, view the image at http://localhost:1337/media/IMAGE_FILE_NAME.

If you see an `413 Request Entity Too Large` error, you'll need to [increase the maximum allowed size of the client request body](https://stackoverflow.com/a/28476755/1799408) in either the server or location context within the Nginx config. Example:

<pre>location / {
    proxy_pass http://hello_django;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $host;
    proxy_redirect off;
    client_max_body_size 100M;
}</pre>

Example:
