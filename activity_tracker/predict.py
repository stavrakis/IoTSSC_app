import pickle
import pandas as pd


class Prediction:

    cols = []

    def __init__(self):
        with open("activity_tracker/model_temporal.pls", 'rb') as pickle_file:
            self.model = pickle.load(pickle_file)
        for i in range(1, 6):
            for s in ['a', 'g']:
                for a in ['x', 'y', 'z']:
                    self.cols.append(s + a + str(i))

    def predict(self, data):

        data = [[data['wrist']] + data['data']]
        return self.model.predict(data)
