import datetime

import pytz
import requests
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

        jwt_token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        jwt_verify = requests.get('https://oauth2.googleapis.com/tokeninfo?id_token=' + jwt_token)
        if jwt_verify.reason != 'OK':
            return HttpResponse(status=403)

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


@csrf_exempt
def get_history(request):
    req = json.loads(request.body)
    if 'start_date' in req:
        start_date = req['start_date']
    else:
        start_date = datetime.datetime.now(tz=pytz.UTC) - datetime.timedelta(days=7)
    if 'end_date' in req:
        end_date = req['end_date']
    else:
        end_date = datetime.datetime.now(tz=pytz.UTC)

    user = get_user(req['token'])
    device = User.objects.get(userName=user).devID
    data = ActivityData.objects.filter(uid=device, time_start__gte=start_date, time_end__lte=end_date)

    datar = [i.json() for i in data]
    reply = json.dumps(datar[::-1])
    #print(reply)
    return HttpResponse("{ 'data': " + reply + "}")


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

    user = Login.objects.filter(userID=user, token=token)
    reply = {}
    if user.count() == 0:
        reply['status'] = 0
        return HttpResponse(json.dumps(reply))
    else:
        reply['status'] = 1
        print(json.dumps(reply))
        return HttpResponse(json.dumps(reply))


@csrf_exempt
def update_fb_token(request):
    data = json.loads(request.body)
    user = data['username']
    token = data['token']
    fb_token = data['fb_token']

    user = Login.objects.filter(userID=user, token=token)
    reply = {}
    if user.count() == 0:
        reply['status'] = 0
        return HttpResponse(json.dumps(reply))
    else:
        user = user.get()
        user.fireBaseToken = data['fb_token']
        user.save()
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


#DEBUG - REMOVE THIS
def notify(request):
    post_data = {
        'to' : 'cY8HCG38RfqzW0QntfbJX-:APA91bEizMff1H8cx2d0tykEso30cLe-0zod29y4QlxiqrqUnHooiu0MUUJQIGCHdUyFxS3kzRNm3ij-OOQxjkOwKDOYwn__vX60pI100fAXIzMjRybR_0vY3B_Qh6zWHLymM_EncSfL',
        'notification': {
            'title': "TITLE",
            'body': 'HELLO'
            }

    }
    headers = {
        'Authorization': 'key=AAAAB_RrceE:APA91bG19E-0-EAz6ebATOVVR_jZvRY0R4RPMcTx6fmG_zIq8obldCgVWaiIHNyUppU-QiDSdTW_TV1KkBwGp3IWjI7VEETxUTVCGvvVeMDoMIvgO9VZs7-jTjY5qcGgfXQYVZ6ccj9q',
        'Content-Type': 'application/json'
    }
    #response = requests.post('https://fcm.googleapis.com/v1/projects/tidy-bindery-303917/messages:send?auth=AAAAB_RrceE:APA91bG19E-0-EAz6ebATOVVR_jZvRY0R4RPMcTx6fmG_zIq8obldCgVWaiIHNyUppU-QiDSdTW_TV1KkBwGp3IWjI7VEETxUTVCGvvVeMDoMIvgO9VZs7-jTjY5qcGgfXQYVZ6ccj9q', data=post_data)
    response = requests.post('https://fcm.googleapis.com/fcm/send', json=post_data, headers=headers)
    print(str(post_data))
    print(str(headers))
    print(response)
    return HttpResponse(str(response.reason))
