"""Generate simple game sounds with pure Python. Run: python make_sounds.py"""
import math
import random
import struct
import wave

RATE = 44100  # samples per second, CD quality


def write_wav(path, samples):
    with wave.open(path, "w") as f:
        f.setnchannels(1)   # mono
        f.setsampwidth(2)   # 16 bit
        f.setframerate(RATE)
        frames = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples
        )
        f.writeframes(frames)


def tone(freq, dur, vol=0.5, attack=0.01, release=0.08):
    """One sine note with a simple envelope (smooth start and end)."""
    out = []
    for i in range(int(RATE * dur)):
        t = i / RATE
        env = min(1.0, t / attack, (dur - t) / release)
        out.append(vol * env * math.sin(2 * math.pi * freq * t))
    return out


def noise(dur, vol=0.3, release=0.04):
    """White noise burst - raw material for footsteps."""
    out = []
    n = int(RATE * dur)
    for i in range(n):
        env = min(1.0, (dur - i / RATE) / release)
        out.append(vol * env * (random.random() * 2 - 1))
    return out


if __name__ == "__main__":
    write_wav("sounds/click.wav", tone(880, 0.05) + tone(1320, 0.06, vol=0.4))
    write_wav("sounds/win.wav",
              tone(523, 0.12) + tone(659, 0.12) + tone(784, 0.12) + tone(1046, 0.4, vol=0.6))
    write_wav("sounds/lose.wav",
              tone(330, 0.18) + tone(262, 0.18) + tone(196, 0.45, vol=0.55))
    write_wav("sounds/step.wav", noise(0.05, vol=0.25, release=0.03))
    write_wav("sounds/ping.wav", tone(600, 0.1, vol=0.35))
    print("done: sounds/")
