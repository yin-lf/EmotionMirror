import os
from abc import ABC, abstractmethod
import numpy as np
from tensorflow.keras.models import Sequential, model_from_json
from tensorflow.keras.layers import LSTM, Dense, Dropout
from ..base import BaseModel

class DNN(BaseModel, ABC):
    def __init__(self, model: Sequential, trained: bool = False) -> None:
        super(DNN, self).__init__(model, trained)

    @classmethod
    def load(cls, path: str, name: str):
        model_json_path = os.path.abspath(os.path.join(path, name + ".json"))
        json_file = open(model_json_path, "r")
        loaded_model_json = json_file.read()
        json_file.close()
        
        custom_objects = {
            'Sequential': Sequential,
            'LSTM': LSTM,
            'Dense': Dense,
            'Dropout': Dropout
        }
        
        model = model_from_json(loaded_model_json, custom_objects=custom_objects)

        model_path = os.path.abspath(os.path.join(path, name + ".h5"))
        model.load_weights(model_path)

        return cls(model, True)

    def predict(self, samples: np.ndarray) -> np.ndarray:
        if not self.trained:
            raise RuntimeError("There is no trained model.")

        samples = self.reshape_input(samples)
        return np.argmax(self.model.predict(samples), axis=1)

    def predict_proba(self, samples: np.ndarray) -> np.ndarray:
        if not self.trained:
            raise RuntimeError('There is no trained model.')

        if hasattr(self, 'reshape_input'):
            samples = self.reshape_input(samples)
        return self.model.predict(samples)[0]

    @abstractmethod
    def reshape_input(self, data: np.ndarray) -> np.ndarray:
        pass