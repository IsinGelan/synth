
"""Only works for PCM ints"""

from math import sin, tau
from typing import Callable, Iterator
from enum import IntEnum

from .helpers import clamp
from .track import to_mono_track

SAMPLE_RATE = 48000

# ======================
class Note(IntEnum):
    C = 0
    Cis = 1
    D = 2
    Dis = 3
    E = 4
    F = 5
    Fis = 6
    G = 7
    Gis = 8
    A = 9
    Ais = 10
    H = 11

def note_to_freq(note: Note, octave: int, *, a4: float = 440) -> float:
    relative_to_a4: int = (octave - 4)*12 + note - Note.A
    rel_octaves, rel_halftones = divmod(relative_to_a4, 12)
    return a4 * pow(2, rel_octaves) * pow(2, rel_halftones / 12)

def str_to_note(one_note_str: str) -> tuple[Note, int]:
    """returns note and octave"""
    suffix = one_note_str[-1]
    has_octave_suffix = suffix.isdecimal()
    octave = int(suffix) if has_octave_suffix else 4
    without_suffix = one_note_str[:-1] if has_octave_suffix else one_note_str
    note_res = Note.__members__.get(without_suffix.capitalize())
    if note_res is None:
        raise ValueError(f"`{one_note_str}` is not a valid note string!")
    return (note_res, octave)

def note_str_to_freqs(note_str: str, *, a4: float = 440) -> list[float]:
    """read in a string of notes, e.g. `"c e g"` or `c2 a3 gis`\n
    (octave number defaults to `4`)\n
    returns: the corresponding frequencies"""
    return [note_to_freq(*str_to_note(note), a4=a4) for note in note_str.split(" ")]


# ======================
def silence(dur_s: float) -> Iterator[float]:
    sample_n = int(SAMPLE_RATE * dur_s)
    for _ in range(sample_n):
        yield 0

# @to_mono_track
def one_frequency(f: float, dur_s: float, vol: float, *, phase: float = 0) -> Iterator[float]:
    assert 20 <= f <= 20000

    sample_n = int(SAMPLE_RATE * dur_s)
    for i in range(sample_n):
        t = i/SAMPLE_RATE
        y = vol * sin(tau * f * t + phase)
        yield y

# @to_mono_track
def multiple_frequencies(fs: list[tuple[float]], dur_s: float, vol: float = 1, *, phases: list[float] = ...) -> Iterator[float]:
    n = len(fs)
    if phases == ...:
        phases = [0]*n
    assert len(phases) == n

    sample_n = int(SAMPLE_RATE * dur_s)
    for i in range(sample_n):
        t = i/SAMPLE_RATE
        y = vol/n * sum(sin(tau * freq * t + phase) for freq, phase in zip(fs, phases))
        yield y

# @to_mono_track
def evolving_frequency(t_f_func: Callable[[float], float], dur_s: float, vol: float = 1) -> Iterator[float]:
    """f_func gives the frequency at each point"""
    sample_n = SAMPLE_RATE * dur_s
    phase = 0 # in range [0, 1)

    dt = 1/SAMPLE_RATE

    for i in range(sample_n):
        t = i*dt
        f = clamp(t_f_func(t), 20, 20000)
        phase += dt*f  # T = 1/f; dt/T
        phase %= 1
        y = vol*sin(tau*phase)
        yield y
