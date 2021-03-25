import datetime

import pytz
import requests
from django.http import HttpResponse
from .models import ActivityData, User, Login
import base64
import json
from .predict import Prediction
from .logger import ActivityLogger
from .user_auth import user_login, user_register, get_user
from django.views.decorators.csrf import csrf_exempt

prd = Prediction()
devices = ActivityLogger()


def index(request):
    return HttpResponse("Activity tracker index")


@csrf_exempt
def pub(request):
    """
    Receives sensor data from Google Pub/Sub. Subscription must authenticate using JWT token.
    """
    if request.method == 'POST':

        # Verify Pub/Sub JWT auth token
        jwt_token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
        jwt_verify = requests.get('https://oauth2.googleapis.com/tokeninfo?id_token=' + jwt_token)
        token = json.loads(jwt_verify.content)
        if jwt_verify.reason != 'OK' or token['email'] != 'tidy-bindery-303917@appspot.gserviceaccount.com':
            return HttpResponse(status=403)

        data = json.loads(request.body)
        deviceId = data['message']['attributes']['deviceId']
        sensor_data = json.loads(base64.b64decode(data['message']['data']).decode('utf-8'))

        # Perform predicton
        pred = prd.predict(sensor_data)
        print(deviceId + " : " + str(pred))
        devices.log(deviceId, pred, int(sensor_data['date']))

    return HttpResponse(status=200)


def get_now(request):
    """
    Return current activity for user corresponding to login token
    """
    reply = {'status': '0'}

    # Validate user token
    if 'token' not in request.GET:
        return HttpResponse(json.dumps(reply))
    user = get_user(request.GET['token'])
    if user is False:
        return HttpResponse(json.dumps(reply))

    device_id = User.objects.filter(userName=user).get().devID
    # Get activity within last 7 seconds
    activity_now = ActivityData.objects.filter(uid=device_id, time_end__gte=(datetime.datetime.now(tz=pytz.UTC) - datetime.timedelta(seconds=7)))
    if activity_now.count() == 0:
        reply['status'] = 1
        reply['activity'] = 'none'
        return HttpResponse(json.dumps(reply))
    else:
        reply['status'] = 1
        reply['activity'] = activity_now.first().activity
        return HttpResponse(json.dumps(reply))


@csrf_exempt
def get_history(request):
    """
    Returns activity history within given date/time range. If range not specified, defaults to 7 days
    """
    req = json.loads(request.body)

    # Only count exercise time within current day
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

    # Format history to JSON
    datar = [i.json() for i in data]
    reply = json.dumps(datar[::-1])
    return HttpResponse("{ 'data': " + reply + "}")


@csrf_exempt
def login(request):
    """
    Authenticates user and returns a login token
    """

    # Verify user credentials
    if 'user' in request.GET and 'pass' in request.GET:
        user = request.GET['user']
        password = request.GET['pass']
    else:
        data = json.loads(request.body)
        user = data['username']
        password = data['password']

    # Generate user token if user exists
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
    """
    Check if login token is valid
    """
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
        return HttpResponse(json.dumps(reply))


@csrf_exempt
def update_fb_token(request):
    """
    Update Firebase Registration Token
    """
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
    """
    Register a new user account. Requires username, password, device name
    """
    reply = {'status': 0}

    # Ensure all details are supplied
    data = json.loads(request.body)
    if not all(key in data for key in ['user', 'pass', 'device']):
        reply['message'] = 'One or more fields not specified'
        return HttpResponse(json.dumps(reply))

    # Attempt register and return status
    if user_register(data['user'], data['pass'], data['device']) is True:
        reply['user'] = data['user']
        reply['status'] = 1
        return HttpResponse(json.dumps(reply))

    reply['message'] = 'Could not register'
    return HttpResponse(json.dumps(reply))

