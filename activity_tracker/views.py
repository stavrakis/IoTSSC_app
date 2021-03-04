from django.shortcuts import render
from django.http import HttpResponse
from .models import SensorData
import base64
import json

def index(request):
    return HttpResponse("Hello, world. You're at the activity tracker index.")


def viewdb(request):
    limit = 0
    limit_arg = request.GET.get('last')
    if limit_arg and limit_arg < 5000:
        limit = limit_arg + 1
    else:
        limit = 201

    resp = SensorData.objects.all()[:limit]
    out = '<br />'.join([r for r in resp])
    return HttpResponse(out)


def pub(request):
    print('pub called')
    data = request.POST.get()
    pubsub_message = base64.b64decode(data.decode('utf-8'))
    jsondata = json.loads(pubsub_message)
    print(pubsub_message)

#def getvalue(request):
#    request =