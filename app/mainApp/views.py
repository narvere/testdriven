from django.http import HttpResponse
from django.shortcuts import render


def start_page(request):
    return HttpResponse("Hello world")


def time(request):
    return render(request, "time.html")
