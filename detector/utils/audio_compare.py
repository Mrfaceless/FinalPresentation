import librosa
import numpy as np
from scipy.spatial.distance import cosine

def extract_mfcc(file_path, sr=22050, n_mfcc=13):
    y, sr = librosa.load(file_path, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return np.mean(mfcc.T, axis=0)  # Taking  the mean  time

def compare_audio(file1_path, file2_path):
    try:
        mfcc1 = extract_mfcc(file1_path)
        mfcc2 = extract_mfcc(file2_path)

        # Compute cosine similarity
        similarity = 1 - cosine(mfcc1, mfcc2)
        similarity_percent = round(similarity * 100, 2)

        return similarity_percent
    except Exception as e:
        print(f"Error comparing files: {e}")
        return 0.0
