"""
Audio Chime Generator for Tewabu ERP.
Synthesizes a pleasant ascending chord audio chime (WAV) in memory
for success feedback upon design & order registration.
"""

import io
import math
import struct
import wave

_CACHED_CHIME_BYTES: bytes | None = None

def get_chime_bytes() -> bytes:
    """Generate or return cached in-memory pleasant success chime WAV bytes."""
    global _CACHED_CHIME_BYTES
    if _CACHED_CHIME_BYTES is not None:
        return _CACHED_CHIME_BYTES

    sample_rate = 44100
    # Three-note rising chord: C5 (523.25 Hz), E5 (659.25 Hz), G5 (783.99 Hz)
    notes = [
        (523.25, 0.12),
        (659.25, 0.12),
        (783.99, 0.40),
    ]

    audio_data = bytearray()
    for freq, duration in notes:
        num_frames = int(sample_rate * duration)
        for i in range(num_frames):
            t = float(i) / sample_rate
            envelope = math.exp(-3.5 * (t / duration))
            val = (
                0.7 * math.sin(2.0 * math.pi * freq * t) +
                0.3 * math.sin(2.0 * math.pi * freq * 2 * t)
            ) * envelope
            sample = int(val * 24000)
            audio_data.extend(struct.pack('<h', max(-32767, min(32767, sample))))

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)

    _CACHED_CHIME_BYTES = buf.getvalue()
    return _CACHED_CHIME_BYTES
