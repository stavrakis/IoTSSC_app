import datetime

import pytz
from django.http import HttpResponse
from .models import ActivityData, User, Login
import base64
import json
from .predict import Prediction
from .logger import ActivityLogger, process_milestones
from .user_auth import user_login, user_register, get_user
from django.views.decorators.csrf import csrf_exempt

prd = Prediction()
devices = ActivityLogger()


def index(request):
    return HttpResponse("Hello, world. You're at the activity tracker index.")


def viewdb(request):
    limit = 0
    limit_arg = request.GET.get('last')
    if limit_arg is not None and int(limit_arg) < 5000:
        limit = int(limit_arg)
    else:
        limit = 20

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


def get_now(request):
    reply = {'status': '0'}
    if 'token' not in request.GET:
        return HttpResponse(json.dumps(reply))
    user = get_user(request.GET['token'])
    if user is False:
        return HttpResponse(json.dumps(reply))

    device_id = User.objects.filter(userName=user).get().devID
    activity_now = ActivityData.objects.filter(uid=device_id, time_end__gte=(datetime.datetime.now(tz=pytz.UTC) - datetime.timedelta(seconds=12)))
    if activity_now.count() == 0:
        reply['status'] = 1
        reply['activity'] = 'none'
        return HttpResponse(json.dumps(reply))
    else:
        reply['status'] = 1
        reply['activity'] = activity_now.get().activity
        return HttpResponse(json.dumps(reply))


def get_history(request):
    if 'start_date' in request.GET:
        start_date = request.GET['start_date']
    if 'end_date' in request.GET:
        end_date = request.GET['end_date']

@csrf_exempt
def login(request):
    #if 'user' not in request.GET or 'pass' not in request.GET:
    #    return HttpResponse(status=403)

    if 'user' in request.GET and 'pass' in request.GET:
        user = request.GET['user']
        password = request.GET['pass']
    else:
        data = json.loads(request.body)
        user = data['username']
        password = data['password']
        #print(user + " " + password)

    user_token = user_login(user, password)
    reply = {}
    if user_token is None:
        reply['status'] = 0
        return HttpResponse(json.dumps(reply))
    else:
        reply['status'] = 1
        reply['token'] = user_token
        return HttpResponse(json.dumps(reply))


@csrf_exempt
def check_token(request):
    data = json.loads(request.body)
    user = data['username']
    token = data['token']

    user = Login.objects.get(userID=user, token=token)
    reply = {}
    if user is None:
        reply['status'] = 0
        return HttpResponse(json.dumps(reply))
    else:
        reply['status'] = 1
        return HttpResponse(json.dumps(reply))


def register(request):
    reply = {'status': 0}
    if not all(key in request.GET for key in ['user', 'pass', 'device']):
        reply['message'] = 'One or more fields not specified'
        return HttpResponse(json.dumps(reply))

    if user_register(request.GET['user'], request.GET['pass'], request.GET['device']) is True:
        reply['user'] = request.GET['user']
        reply['status'] = 1
        return HttpResponse(json.dumps(reply))

    reply['message'] = 'Could not register'
    return HttpResponse(json.dumps(reply))


def proc_mil(request):
    user = User.objects.filter(userName=request.GET['user']).get()
    process_milestones(user)
    return HttpResponse(status=200)