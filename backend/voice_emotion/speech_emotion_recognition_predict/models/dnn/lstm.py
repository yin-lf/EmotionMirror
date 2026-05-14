from tensorflow.keras.layers import LSTM as KERAS_LSTM
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
import numpy as np
from .dnn import DNN

class LSTM(DNN):
    def __init__(self, model: Sequential, trained: bool = False) -> None:
        super(LSTM, self).__init__(model, trained)

    def reshape_input(self, data: np.ndarray) -> np.ndarray:
        return np.reshape(data, (data.shape[0], 1, data.shape[1]))