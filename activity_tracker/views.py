from django.shortcuts import render
from django.http import HttpResponse
from .models import ActivityData
import base64
import json
from .predict import Prediction
from .logger import ActivityLogger
from django.views.decorators.csrf import csrf_exempt

prd = Prediction()
devices = ActivityLogger()


def index(request):
    return HttpResponse("Hello, world. You're at the activity tracker index.")


def viewdb(request):
    limit = 0
    limit_arg = request.GET.get('last')
    if limit_arg and limit_arg < 5000:
        limit = limit_arg + 1
    else:
        limit = 201

    resp = ActivityData.objects.all()[:limit]
    out = 'Data <br />'
    for r in resp:
        out += str(r) + '<br />'
    return HttpResponse(out)


@csrf_exempt
def pub(request):
    if request.method == 'POST':

        data = json.loads(request.body)
        deviceId = data['message']['attributes']['deviceId']
        sensor_data = json.loads(base64.b64decode(data['message']['data']).decode('utf-8'))

        pred = prd.predict(sensor_data)
        print(deviceId + " : " + str(pred))
        devices.log(deviceId, pred, int(sensor_data['date']))

    return HttpResponse(status=200)
