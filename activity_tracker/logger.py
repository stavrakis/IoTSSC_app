from datetime import datetime
import pytz
from statistics import mode, StatisticsError
import numpy as np
from .models import ActivityData
from django.db.models import Max


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
        self.update_activity_db(device_id=device_id, activity=act, time_start=time_start, time_end=time_end)

    def update_activity_db(self, device_id, activity, time_start, time_end):
        if len(ActivityData.objects.filter(uid=device_id)) == 0:
            ActivityData(uid=device_id, activity=activity, time_start=time_start, time_end=time_end).save()
        else:
            last_act = ActivityData.objects.get(uid=device_id, time_end=ActivityData.objects.filter(uid=device_id).aggregate(Max('time_end'))['time_end__max'])
            if last_act.activity == activity and (time_start - last_act.time_end).total_seconds() < 10:
                last_act.time_end = time_end
                last_act.save()
            else:
                ActivityData(uid=device_id, activity=activity, time_start=time_start, time_end=time_end).save()
