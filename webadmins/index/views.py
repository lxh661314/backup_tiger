from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
import os
import time

from index.task import f1

# Create your views here.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(os.path.join(BASE_DIR, 'static'), 'upload')


def index(request):
    return HttpResponse("this is index")


def celery_index(request):
    # r = f1.delay()
    f1()
    # print(r)
    return HttpResponse("this is index page!")


def hello(request):
    state_time = time.time()
    data = {
        "state_time": state_time,
        "books": ["python", "java", "go"]
    }


