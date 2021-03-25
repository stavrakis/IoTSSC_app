from datetime import datetime, date, time, timedelta
import pytz
from statistics import mode, StatisticsError
import numpy as np
import requests

from .models import ActivityData, User, Milestone, Login
from django.db.models import Max, Q


def update_activity_db(device_id, activity, time_start, time_end):
    """
    Updates database with new activity

        Parameters:
            device_id (str): Unique identifier of device
            activity (int): Activity type
            time_start (datetime): Date & time activity starts
            time_end (datetime): Date & time activity ends
    """
    if len(ActivityData.objects.filter(uid=device_id)) == 0: # If no activity data, initialise record
        ActivityData(uid=device_id, activity=activity, time_start=time_start, time_end=time_end).save()
    else:
        # Get last activity
        last_act = ActivityData.objects.get(uid=device_id, time_end=ActivityData.objects.filter(uid=device_id).aggregate(Max('time_end'))['time_end__max'])

        # Update last activity if continuous
        if last_act.activity == activity and (time_start - last_act.time_end).total_seconds() < 5:
            last_act.time_end = time_end
            last_act.save()
        else:
            ActivityData(uid=device_id, activity=activity, time_start=time_start, time_end=time_end).save()

    user = User.objects.filter(devID=device_id).get()
    process_milestones(user)


def process_milestones(user):
    """
    Calculate milestones and push notifications for new milestones

        Parameters:
            user (User): User model object
    """
    thisdate = datetime(year=date.today().year, month=date.today().month, day=date.today().day, hour=0, minute=0, second=0, tzinfo=pytz.UTC)
    daily_activities = ActivityData.objects.filter(uid=user.devID)
    daily_activities = daily_activities.filter(Q(time_start__year=thisdate.year, time_start__month=thisdate.month, time_start__day=thisdate.day)
                                               |Q(time_end__year=thisdate.year, time_end__month=thisdate.month, time_end__day=thisdate.day))
    time_sum_walk = timedelta(seconds=0)
    time_sum_run = timedelta(seconds=0)

    # Sum all daily activities
    for item in daily_activities:
        if item.time_start < thisdate: # Exclude activity time overlapping previous day
            timestart = thisdate
        else:
            timestart = item.time_start
        if item.time_end > datetime.combine(date=thisdate, time=time(23, 59, 59, tzinfo=pytz.UTC)): # Exclude activity time overlapping with next day
            timeend = datetime.combine(date=thisdate, time=time(23, 59, 59, tzinfo=pytz.UTC))
        else:
            timeend = item.time_end
        if item.activity == 0:
            time_sum_walk += timeend - timestart
        elif item.activity == 1:
            time_sum_run += timeend - timestart

    print('Processing daily milestones for user ' + user.userName + '  run: ' + str(time_sum_run) + ' walk: ' + str(time_sum_walk))
    if time_sum_run > timedelta(minutes=1):
        run_milestone = Milestone.objects.filter(user=user.userName, type=3, date=thisdate)
        if run_milestone.count() == 0: # New milestone, must be recorded
            new_daily_run_milestone = Milestone(user=user.userName, type=3, date=thisdate, data=str(time_sum_run)).save()
            notify(user, "Daily goal achieved!", "Running")
        else: # Update existing milestone
            run_milestone = run_milestone.get()
            run_milestone.data = str(time_sum_run)
            run_milestone.save()

    if time_sum_walk > timedelta(minutes=1):
        walk_milestone = Milestone.objects.filter(user=user.userName, type=2, date=thisdate)
        if walk_milestone.count() == 0: # New milestone, must be recorded
            new_daily_walk_milestone = Milestone(user=user.userName, type=2, date=thisdate, data=str(time_sum_walk)).save()
            notify(user, "Daily goal achieved!", "Walking")
        else: # Update existing milestone
            walk_milestone = walk_milestone.get()
            walk_milestone.data = str(time_sum_walk)
            walk_milestone.save()


class ActivityLogger:
    """
    Buffers activities and updates database periodically
    """

    def __init__(self):
        self.deviceData = {}

    def log(self, device_id, activity, time):
        """
        Add activities to temporary buffer and process when enough have been collected

            Parameters:
                device_id (str): Unique identifier of device
                activity (int): Activity type\
                time (int): Unix timestamp
        """
        if device_id not in self.deviceData:
            self.deviceData[device_id] = {}
            self.deviceData[device_id]['data'] = []

        # Process past activity that remained in buffer
        if len(self.deviceData[device_id]['data']) > 0 and time - int(self.deviceData[device_id]['data'][-1][1]) > 5:
            self.process_activity(device_id)

        # Buffer data until 5 readings are received
        self.deviceData[device_id]['data'].append([activity, time])
        if len(self.deviceData[device_id]['data']) >= 5:
            self.process_activity(device_id)

    def process_activity(self, device_id):
        """
        Process activity, find most common activity prediction within window

            Parameters:
                device_id (str): Unique identifier of device
        """
        # Put all predictions in list and average
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
        update_activity_db(device_id=device_id, activity=act, time_start=time_start, time_end=time_end)
        print('Activity logged for ' + device_id + ' : ' + str(act) + ' between ' + str(time_start) + ' - ' + str(
            time_end))


def notify(user, title, body):
    """
    Create push notification (used for milestone achievement)

        Parameters:
            user (User): User model object
            title (str): Title of notification
            body (str): Main body of notification
    """
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
