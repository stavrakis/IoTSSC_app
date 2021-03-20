from datetime import datetime, date, time, timedelta
import pytz
from statistics import mode, StatisticsError
import numpy as np
import requests

from .models import ActivityData, User, Milestone, Login
from django.db.models import Max, Q


def update_activity_db(device_id, activity, time_start, time_end):
    if len(ActivityData.objects.filter(uid=device_id)) == 0:
        ActivityData(uid=device_id, activity=activity, time_start=time_start, time_end=time_end).save()
    else:
        last_act = ActivityData.objects.get(uid=device_id, time_end=ActivityData.objects.filter(uid=device_id).aggregate(Max('time_end'))['time_end__max'])
        if last_act.activity == activity and (time_start - last_act.time_end).total_seconds() < 10:
            last_act.time_end = time_end
            last_act.save()
        else:
            ActivityData(uid=device_id, activity=activity, time_start=time_start, time_end=time_end).save()

    user = User.objects.filter(devID=device_id).get()
    process_milestones(user)


def process_milestones(user):
    thisdate = datetime(year=date.today().year, month=date.today().month, day=date.today().day, hour=0, minute=0, second=0, tzinfo=pytz.UTC)
    daily_activities = ActivityData.objects.filter(uid=user.devID)
    #print('daily1 ' + str(daily_activities.count()))
    daily_activities = daily_activities.filter(Q(time_start__year=thisdate.year, time_start__month=thisdate.month, time_start__day=thisdate.day)
                                               |Q(time_end__year=thisdate.year, time_end__month=thisdate.month, time_end__day=thisdate.day))
    time_sum_walk = timedelta(seconds=0)
    time_sum_run = timedelta(seconds=0)
    #print("daily activities: " + str(daily_activities.count()))
    for item in daily_activities:
        if item.time_start < thisdate:
            timestart = thisdate
        else:
            timestart = item.time_start
        if item.time_end > datetime.combine(date=thisdate, time=time(23, 59, 59, tzinfo=pytz.UTC)):
            timeend = datetime.combine(date=thisdate, time=time(23, 59, 59, tzinfo=pytz.UTC))
        else:
            timeend = item.time_end
        #print('start: ' + str(timestart) + ' end: ' + str(timeend))
        if item.activity == 0:
            time_sum_walk += timeend - timestart
        elif item.activity == 1:
            time_sum_run += timeend - timestart

    print('Processing daily milestones for user ' + user.userName + '  run: ' + str(time_sum_run) + ' walk: ' + str(time_sum_walk))
    if time_sum_run > timedelta(minutes=1):
        run_milestone = Milestone.objects.filter(user=user.userName, type=3, date=thisdate)
        if run_milestone.count() == 0:
            new_daily_run_milestone = Milestone(user=user.userName, type=3, date=thisdate, data=str(time_sum_run)).save()
            notify(user, "Daily goal achieved!", "Running")
        else:
            run_milestone = run_milestone.get()
            run_milestone.data = str(time_sum_run)
            run_milestone.save()

    if time_sum_walk > timedelta(minutes=1):
        walk_milestone = Milestone.objects.filter(user=user.userName, type=2, date=thisdate)
        if walk_milestone.count() == 0:
            new_daily_walk_milestone = Milestone(user=user.userName, type=2, date=thisdate, data=str(time_sum_walk)).save()
            notify(user, "Daily goal achieved!", "Walking")
        else:
            walk_milestone = walk_milestone.get()
            walk_milestone.data = str(time_sum_walk)
            walk_milestone.save()


class ActivityLogger:

    def __init__(self):
        self.deviceData = {}

    def log(self, device_id, activity, time):
        if device_id not in self.deviceData:
            self.deviceData[device_id] = {}
            self.deviceData[device_id]['data'] = []

        #if len(self.deviceData[device_id]['data']) > 0:
            #print(self.deviceData[device_id]['data'])
        #print(len(self.deviceData[device_id]['data']))
        if len(self.deviceData[device_id]['data']) > 0 and time - int(self.deviceData[device_id]['data'][-1][1]) > 10:
            self.process_activity(device_id)

        self.deviceData[device_id]['data'].append([activity, time])
        if len(self.deviceData[device_id]['data']) >= 10:
            self.process_activity(device_id)

    def process_activity(self, device_id):
        activities = np.array([l[0] for l in self.deviceData[device_id]['data']]).flatten()
        try:
            act = mode(activities)
        except StatisticsError as e:
            print(e)
            print(activities)
            act = 1

        time_start = datetime.fromtimestamp(self.deviceData[device_id]['data'][0][1]).replace(tzinfo=pytz.UTC)
        time_end = datetime.fromtimestamp(self.deviceData[device_id]['data'][-1][1]).replace(tzinfo=pytz.UTC)

        self.deviceData[device_id]['data'] = []
        print('Activity logged for ' + device_id + ' : ' + str(act) + ' between ' + str(time_start) + ' - ' + str(time_end))
        update_activity_db(device_id=device_id, activity=act, time_start=time_start, time_end=time_end)


def notify(user, title, body):
    device_login = Login.objects.get(userID=user.userName)
    post_data = {
        'to': device_login.fireBaseToken,
        'notification': {
            'title': title,
            'body': body
        }

    }
    headers = {
        'Authorization': 'key=AAAAB_RrceE:APA91bG19E-0-EAz6ebATOVVR_jZvRY0R4RPMcTx6fmG_zIq8obldCgVWaiIHNyUppU-QiDSdTW_TV1KkBwGp3IWjI7VEETxUTVCGvvVeMDoMIvgO9VZs7-jTjY5qcGgfXQYVZ6ccj9q',
        'Content-Type': 'application/json'
    }
    response = requests.post('https://fcm.googleapis.com/fcm/send', json=post_data, headers=headers)