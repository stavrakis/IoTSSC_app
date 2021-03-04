import pickle
from sklearn import svm


class Prediction:

    def __init__(self):
        with open("activity_tracker/model.pls", 'rb') as pickle_file:
            self.model = pickle.load(pickle_file)

    def predict(self, data):
        data_point = [[data['wrist'], data['accel_x'], data['accel_y'], data['accel_z'], data['gyro_x'], data['gyro_y'], data['gyro_z'] ]]
        return self.model.predict(data_point)
