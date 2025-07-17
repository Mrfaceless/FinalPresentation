import numpy as np
from scipy.ndimage import maximum_filter
from pydub import AudioSegment
import hashlib
from scipy.signal import stft


def generate_hashes(file_path, fan_value=15, amp_min=10):
    """
    Generate audio fingerprints from a time-frequency spectrogram.
    Returns a list of (hash, offset) tuples.
    """
    # Load and preprocess the audio
    audio = AudioSegment.from_file(file_path)
    print(f"[DEBUG] Original audio: channels={audio.channels}, "
          f"frame_rate={audio.frame_rate}, duration={len(audio) / 1000:.2f}s")

    # Convert to mono and downsample for efficiency
    audio = audio.set_channels(1).set_frame_rate(8000)
    samples = np.array(audio.get_array_of_samples())

    # Compute the STFT
    f, t, Zxx = stft(samples, fs=8000, nperseg=512)
    magnitude = np.abs(Zxx)

    # Find local maxima (peaks)
    neighborhood_size = (20, 20)
    local_max = maximum_filter(magnitude, size=neighborhood_size) == magnitude
    peak_coords = np.argwhere(local_max)
    print(f"[DEBUG] Found {len(peak_coords)} local peaks")

    # Extract peaks above amplitude threshold
    peaks = [(f[i], t[j]) for i, j in peak_coords if magnitude[i][j] > amp_min]
    print(f"[DEBUG] Retained {len(peaks)} peaks above amplitude threshold {amp_min}")

    # Generate fingerprint hashes from peaks
    hashes = []
    for i in range(len(peaks)):
        for j in range(1, fan_value):
            if i + j < len(peaks):
                f1, t1 = peaks[i]
                f2, t2 = peaks[i + j]
                delta_t = round(t2 - t1, 2)
                if delta_t <= 10:
                    hash_input = f"{int(f1)}|{int(f2)}|{delta_t}"
                    h = hashlib.sha1(hash_input.encode()).hexdigest()[:20]
                    hashes.append((h, round(t1, 2)))

    print(f"[DEBUG] Generated {len(hashes)} hashes")

    return hashes
