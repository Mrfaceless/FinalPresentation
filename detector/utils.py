# detector/utils.py
import librosa
import numpy as np
from .models import CopyrightedMusic

def extract_features(audio_path):
    """Extract musical features from audio file"""
    y, sr = librosa.load(audio_path)
    
    # Extract features
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    
    return {
        'tempo': tempo,
        'chroma': chroma,
        'mfcc': mfcc
    }

def compare_features(features1, features2):
    """Compare two sets of musical features"""
    # Compare chroma features
    chroma_sim = np.mean([
        1 - librosa.segment.cross_similarity(
            features1['chroma'], 
            features2['chroma']
        )
    ])
    
    # Compare MFCC features
    mfcc_sim = np.mean([
        1 - librosa.segment.cross_similarity(
            features1['mfcc'], 
            features2['mfcc']
        )
    ])
    
    # Tempo similarity
    tempo_sim = 1 - abs(features1['tempo'] - features2['tempo']) / max(
        features1['tempo'], 
        features2['tempo']
    )
    
    # Weighted average of similarities
    similarity_score = 0.4 * chroma_sim + 0.4 * mfcc_sim + 0.2 * tempo_sim
    
    return similarity_score * 100  # Convert to percentage

def analyze_music(audio_path):
    """Analyze a music file against copyrighted works"""
    # Extract features from uploaded file
    uploaded_features = extract_features(audio_path)
    
    results = []
    
    # Compare with all copyrighted works
    for copyrighted in CopyrightedMusic.objects.all():
        # Extract features from copyrighted work
        copyrighted_features = extract_features(copyrighted.audio_file.path)
        
        # Compare features
        similarity_score = compare_features(uploaded_features, copyrighted_features)
        
        if similarity_score > 50:  # Only report significant similarities
            results.append({
                'copyrighted_music': copyrighted,
                'similarity_score': similarity_score,
                'notes': f"Potential match with {copyrighted.title}"
            })
    
    return results