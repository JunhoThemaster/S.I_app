# utils.py
import tempfile
import wave

def save_wave_and_transcribe(pcm_data: bytes, sample_rate: int, model):
    # 1. 임시 WAV 파일로 저장
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        with wave.open(f, "wb") as wf:
            wf.setnchannels(1)             # mono
            wf.setsampwidth(2)             # 16-bit
            wf.setframerate(sample_rate)   # 16kHz
            wf.writeframes(pcm_data)
        path = f.name

    # 2. Whisper로 전사
    segments, _ = model.transcribe(path)
    text = " ".join([seg.text for seg in segments])
    return text.strip()
