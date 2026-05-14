from .dnn import LSTM

_MODELS = {
    'lstm': LSTM,
}

def load(config):
    return _MODELS[config.model].load(
        path = config.checkpoint_path,
        name = config.checkpoint_name
    )