from django.db import models


# Create your models here.

class ActivityData(models.Model):
    uid = models.TextField()
    activity = models.IntegerField()
    time_start = models.DateTimeField()
    time_end = models.DateTimeField()

    def __str__(self):
        out = "(uid={}, activity={}, time_start={}, time_end={})".format(self.uid, self.activity, self.time_start, self.time_end)
        return out


class Milestone(models.Model):
    user = models.TextField()
    type = models.IntegerField()
    date = models.DateField()
    data = models.TimeField()


class User(models.Model):
    userName = models.TextField()
    password = models.TextField()
    devID = models.TextField()


class Login(models.Model):
    userID = models.TextField()
    token = models.TextField()
