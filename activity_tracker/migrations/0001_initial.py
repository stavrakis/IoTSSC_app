# Generated by Django 3.1.7 on 2021-03-04 00:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SensorData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accel_x', models.FloatField()),
                ('accel_y', models.FloatField()),
                ('accel_z', models.FloatField()),
                ('gyro_x', models.FloatField()),
                ('gyro_y', models.FloatField()),
                ('gyro_z', models.FloatField()),
                ('wrist', models.IntegerField()),
                ('time', models.DateTimeField()),
            ],
        ),
    ]
