import numpy as np
import tempfile
import wave
import librosa

def save_wave_and_transcribe_from_path(path: str, sample_rate: int, model):
    import soundfile as sf
    from scipy.signal import resample_poly
    import numpy as np

    y, sr = sf.read(path)
    if y.ndim > 1:
        y = y.mean(axis=1)
    if sr != sample_rate:
        y = resample_poly(y, sample_rate, sr)
    y = y.astype(np.float32)

    segments, _ = model.transcribe(y, language="ko")
    return " ".join([seg.text for seg in segments])