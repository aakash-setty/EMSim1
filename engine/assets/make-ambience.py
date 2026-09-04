#!/usr/bin/env python3
"""Derive engine/ambience.txt from the author's ward recording. Run once; kept so the
loop can be recut.

    ffmpeg -i <source>.mp3 -ac 1 -ar 22050 -f wav mono.wav
    python3 make-ambience.py mono.wav loop.wav
    ffmpeg -i loop.wav -ac 1 -ar 22050 -b:a 48k ambience.mp3
    base64 -w0 ambience.mp3 > engine/ambience.txt

Three decisions, none of them arbitrary.

WHERE. T0 is picked from a two-second RMS profile of the source: a stretch with a steady
level and no transient, so that nothing recognisable recurs every forty-five seconds. The
profile of the original ran between -21 and -31 dB and the stretch from 42 s is among the
flattest of it.

THE SEAM. The tail is crossfaded onto the head with an equal-power curve, so the loop
point is continuous in level as well as in sample value. Equal-power rather than linear
because a linear crossfade of two uncorrelated signals dips about 3 dB in the middle, and
a dip once every forty-five seconds is exactly the sort of thing an ear locks onto.

THE LEVEL. Peak-normalised to 0.95, so that the gain figure in the audio module is against
a known reference rather than against whatever this particular recording happened to be.
Change the recording and the loop still arrives at the same loudness.
"""
import sys, wave, numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
T0, LOOP, XF = 42.0, 45.0, 3.0          # seconds: start, loop length, crossfade

w = wave.open(SRC); sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
i0, L, X = int(T0 * sr), int(LOOP * sr), int(XF * sr)
seg = a[i0:i0 + L + X].copy()
if len(seg) < L + X:
    raise SystemExit("source is too short for T0 + LOOP + XF")

t = np.linspace(0, 1, X, endpoint=False)
seg[:X] = seg[:X] * np.sin(t * np.pi / 2) + seg[L:L + X] * np.cos(t * np.pi / 2)
loop = seg[:L]
loop *= 0.95 / np.abs(loop).max()

rms = float(np.sqrt((loop ** 2).mean()))
print("loop %.1f s  peak %.3f  rms %.4f (%.1f dBFS)"
      % (len(loop) / sr, np.abs(loop).max(), rms, 20 * np.log10(rms)))
o = wave.open(OUT, "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
o.writeframes((loop * 32767).astype(np.int16).tobytes()); o.close()
