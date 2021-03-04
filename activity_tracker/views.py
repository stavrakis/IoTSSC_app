from django.shortcuts import render
from django.http import HttpResponse
from .models import SensorData
from ast import literal_eval
import base64
import json
from .predict import Prediction
from django.views.decorators.csrf import csrf_exempt

prd = Prediction()


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


@csrf_exempt
def pub(request):
    if request.method == 'POST':

        data = json.loads(request.body)
        sensor_data = base64.b64decode(data['message']['data']).decode('utf-8')
        sensor_data = json.loads(sensor_data)
        del sensor_data['time']
        pred = prd.predict(sensor_data)
        print(pred)

    return HttpResponse(status=200)


#def getvalue(request):
#    request =