from abc import ABC, abstractmethod
from typing import Union
import numpy as np
from tensorflow.keras.models import Sequential
from sklearn.metrics import accuracy_score
from sklearn.base import BaseEstimator

class BaseModel(ABC):
    def __init__(self, model: Union[Sequential, BaseEstimator], trained: bool = False) -> None:
        self.model = model
        self.trained = trained

    @abstractmethod
    def predict(self, samples: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def predict_proba(self, samples: np.ndarray) -> np.ndarray:
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: str, name: str):
        pass