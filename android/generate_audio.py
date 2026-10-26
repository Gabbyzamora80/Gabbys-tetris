# SPDX-License-Identifier: GPL-3.0-only
"""Regenerate the mobile game's PCM WAV soundtrack and sound effects."""

from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path


SAMPLE_RATE = 22050
MELODY = (
    659, 494, 523, 587, 523, 494, 440, 440,
    523, 659, 587, 523, 494, 494, 523, 587,
    659, 523, 440, 440, 523, 587, 659, 587,
    523, 494, 523, 587, 659, 523, 440, 440,
)
OUTPUT = Path(__file__).resolve().parent


def tone(notes: tuple[int, ...], duration: float, volume: float) -> array:
    samples = array("h")
    note_length = int(SAMPLE_RATE * duration)
    for frequency in notes:
        for index in range(note_length):
            fade_in = min(1.0, index / (SAMPLE_RATE * 0.004))
            fade_out = min(1.0, (note_length - index) / (SAMPLE_RATE * 0.018))
            envelope = min(fade_in, fade_out)
            phase = 2 * math.pi * frequency * index / SAMPLE_RATE
            wave_value = 1.0 if math.sin(phase) >= 0 else -1.0
            samples.append(int(wave_value * volume * envelope * 32767))
    return samples


def music() -> array:
    samples = array("h")
    beat_length = int(SAMPLE_RATE * 0.17)
    bass_notes = (220, 196, 174, 196, 220, 262, 196, 174)
    for beat, frequency in enumerate(MELODY):
        bass = bass_notes[(beat // 4) % len(bass_notes)]
        for index in range(beat_length):
            fade = min(
                1.0,
                index / (SAMPLE_RATE * 0.006),
                (beat_length - index) / (SAMPLE_RATE * 0.012),
            )
            time = index / SAMPLE_RATE
            lead = 1.0 if math.sin(2 * math.pi * frequency * time) >= 0 else -1.0
            low = 1.0 if math.sin(2 * math.pi * bass * time) >= 0 else -1.0
            samples.append(int((lead * 0.72 + low * 0.28) * 0.10 * fade * 32767))
    return samples


def save_wav(path: Path, samples: array) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(samples.tobytes())


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    save_wav(OUTPUT / "music.wav", music())
    save_wav(OUTPUT / "rotate.wav", tone((660, 880), 0.055, 0.16))
    save_wav(OUTPUT / "drop.wav", tone((420, 300, 190), 0.055, 0.20))
    save_wav(OUTPUT / "lock.wav", tone((250,), 0.075, 0.13))
    save_wav(OUTPUT / "clear.wav", tone((660, 830, 990, 1320), 0.075, 0.18))


if __name__ == "__main__":
    main()
