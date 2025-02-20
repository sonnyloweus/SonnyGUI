import numpy as np
import time

class Cos:
    def __init__(self, config):
        """
        Initialize the Sin function generator.
        :param alpha: Amplitude multiplier
        :param beta: Frequency multiplier
        """
        self.alpha = config["alpha"]
        self.beta = config["beta"]
        self.t = 0

    def compute(self, x):
        return self.alpha * np.sin(self.beta * x)

    ######### DEFINE TEMPLATE CONFIG #########
    config_template = {
        "alpha": 1.0,
        "beta": 1.0,
    }

    experiment_type = {
        "Exp. Class": "Elementary",
    }