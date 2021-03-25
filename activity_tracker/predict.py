import pickle
import pandas as pd


class Prediction:
    """
    Prediction class. Loads model and predicts activities
    """

    cols = []

    def __init__(self):
        # Load pre-trained model
        with open("activity_tracker/model_temporal.pls", 'rb') as pickle_file:
            self.model = pickle.load(pickle_file)

        # Generate column names (accelerometer & gyroscope x,y,z 1-5)
        for i in range(1, 6):
            for s in ['a', 'g']:
                for a in ['x', 'y', 'z']:
                    self.cols.append(s + a + str(i))

    def predict(self, data):
        """
        Performs prediction on given data.

            Parameters:
                data: List of sensor data points
        """
        data = [[data['wrist']] + data['data']]
        return self.model.predict(data)
