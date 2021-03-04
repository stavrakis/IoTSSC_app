from django.db import models


# Create your models here.

class SensorData(models.Model):
    accel_x = models.FloatField()
    accel_y = models.FloatField()
    accel_z = models.FloatField()
    gyro_x = models.FloatField()
    gyro_y = models.FloatField()
    gyro_z = models.FloatField()
    wrist = models.IntegerField()
    time = models.DateTimeField()

    def __str__(self):
        out = "{accel_x:{}, accel_y:{}, accel_z:{}, gyro_x:{}, gyro_y:{}, gyro_z:{}, wrist:{},time:{}}".format(self.accel_x, self.accel_y, self.accel_z, self.gyro_x, self.gyro_y, self.gyro_z, self.wrist, self.time)
        return out
