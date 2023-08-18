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
