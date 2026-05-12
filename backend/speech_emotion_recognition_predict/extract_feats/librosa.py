import os
import librosa
import numpy as np
import pickle
import joblib

def features(X, sample_rate: float) -> np.ndarray:
    stft = np.abs(librosa.stft(X))

    pitches, magnitudes = librosa.piptrack(y=X, sr=sample_rate, S=stft, fmin=70, fmax=400)
    pitch = []
    for i in range(magnitudes.shape[1]):
        index = magnitudes[:, 1].argmax()
        pitch.append(pitches[index, i])

    pitch_tuning_offset = librosa.pitch_tuning(pitches)
    pitchmean = np.mean(pitch)
    pitchstd = np.std(pitch)
    pitchmax = np.max(pitch)
    pitchmin = np.min(pitch)

    cent = librosa.feature.spectral_centroid(y=X, sr=sample_rate)
    cent = cent / np.sum(cent)
    meancent = np.mean(cent)
    stdcent = np.std(cent)
    maxcent = np.max(cent)

    flatness = np.mean(librosa.feature.spectral_flatness(y=X))

    mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=50).T, axis=0)
    mfccsstd = np.std(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=50).T, axis=0)
    mfccmax = np.max(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=50).T, axis=0)

    chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T, axis=0)

    mel = np.mean(librosa.feature.melspectrogram(y=X, sr=sample_rate).T, axis=0)

    contrast = np.mean(librosa.feature.spectral_contrast(S=stft, sr=sample_rate).T, axis=0)

    zerocr = np.mean(librosa.feature.zero_crossing_rate(X))

    S, phase = librosa.magphase(stft)
    meanMagnitude = np.mean(S)
    stdMagnitude = np.std(S)
    maxMagnitude = np.max(S)

    rmse = librosa.feature.rms(S=S)[0]
    meanrms = np.mean(rmse)
    stdrms = np.std(rmse)
    maxrms = np.max(rmse)

    ext_features = np.array([
        flatness, zerocr, meanMagnitude, maxMagnitude, meancent, stdcent,
        maxcent, stdMagnitude, pitchmean, pitchmax, pitchstd,
        pitch_tuning_offset, meanrms, maxrms, stdrms
    ])

    ext_features = np.concatenate((ext_features, mfccs, mfccsstd, mfccmax, chroma, mel, contrast))

    return ext_features

def extract_features(file: str) -> np.ndarray:
    X, sample_rate = librosa.load(file, sr=None)
    return features(X, sample_rate)

def get_data(config, audio_path: str) -> np.ndarray:
    features = extract_features(audio_path)
    feature_path = os.path.join(config.feature_folder, "predict.p")
    os.makedirs(config.feature_folder, exist_ok=True)
    pickle.dump([[audio_path, features, -1]], open(feature_path, 'wb'))
    return load_feature(config)

def load_feature(config) -> np.ndarray:
    feature_path = os.path.join(config.feature_folder, "predict.p")
    features = pickle.load(open(feature_path, 'rb'))
    X = [f[1] for f in features]

    scaler_path = os.path.abspath(os.path.join(config.checkpoint_path, 'SCALER_LIBROSA.m'))
    scaler = joblib.load(scaler_path)
    X = scaler.transform(X)

    return X