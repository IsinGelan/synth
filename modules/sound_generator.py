
"""Only works for PCM ints"""

from itertools import cycle
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
# Phase functions: [0, 1) -> [-1, 1]
FFFunc = Callable[[float], float]

SINE_WAVE = lambda phase: sin(phase)
TRIANG_WAVE = lambda phase: 1 - abs(2 - abs(4*phase - 3))
SQUARE_WAVE = lambda phase: -1 if phase < 0.5 else 1
SAWTOOTH_WAVE = lambda phase: 2 * phase - 1

# ======================
def silence(dur_s: float) -> Iterator[float]:
    sample_n = int(SAMPLE_RATE * dur_s)
    for _ in range(sample_n):
        yield 0

def wave(wave_fun: FFFunc, f: float, dur_s: float, *, vol: float = 1, phase: float = 0) -> Iterator[float]:
    assert 20 <= f <= 20000
    sample_n = int(SAMPLE_RATE * dur_s)
    d_phase = f/SAMPLE_RATE

    for _ in range(sample_n):
        y = wave_fun(phase)
        phase += d_phase
        phase %= 1
        yield vol*y

# @to_mono_track
def sine(f: float, dur_s: float, *, vol: float = 1, phase: float = 0) -> Iterator[float]:
    assert 20 <= f <= 20000

    sample_n = int(SAMPLE_RATE * dur_s)
    for i in range(sample_n):
        t = i/SAMPLE_RATE
        y = vol * sin(tau * f * t + phase)
        yield y

def triang(f: float, dur_s: float, *, vol: float = 1, phase: float = 0) -> Iterator[float]:
    return wave(TRIANG_WAVE, f, dur_s, vol=vol, phase=phase)

def square(f: float, dur_s: float, *, vol: float = 1, phase: float = 0) -> Iterator[float]:
    return wave(SQUARE_WAVE, f, dur_s, vol=vol, phase=phase)

def sawtooth(f: float, dur_s: float, *, vol: float = 1, phase: float = 0) -> Iterator[float]:
    return wave(SAWTOOTH_WAVE, f, dur_s, vol=vol, phase=phase)

def multi_wave(wave: FFFunc, fs: list[float], dur_s: float, *, vols: list[float] = ..., phases: list[float] = ...) -> Iterator[float]:
    n = len(fs)
    if vols == ...:
        vols = [1]*n
    if phases == ...:
        phases = [0]*n
    assert len(phases) == n and len(vols) == n

    sample_n = int(SAMPLE_RATE * dur_s)
    volsum = sum(vols)
    periods = [f/SAMPLE_RATE for f in fs]
    
    current_phases = phases.copy()

    for _ in range(sample_n):
        y = 1/volsum * sum(vol * wave(phase) for vol, phase in zip(vols, current_phases))
        current_phases = [(c + period) % 1 for c, period in zip(current_phases, periods)]
        yield y


# @to_mono_track
def multi_sine(fs: list[float], dur_s: float, *, vols: list[float] = ..., phases: list[float] = ...) -> Iterator[float]:
    n = len(fs)
    if vols == ...:
        vols = [1]*n
    if phases == ...:
        phases = [0]*n
    assert len(phases) == n and len(vols) == n

    sample_n = int(SAMPLE_RATE * dur_s)
    dt = 1/SAMPLE_RATE

    volsum = sum(vols)
    
    for i in range(sample_n):
        t = i*dt
        y = 1/volsum * sum(vol * sin(tau * freq * t + phase) for freq, vol, phase in zip(fs, vols, phases))
        yield y

# @to_mono_track
def evolving_frequency(t_f_func: Callable[[float], float], dur_s: float, *, vol: float = 1) -> Iterator[float]:
    """f_func gives the frequency at each point"""
    sample_n = int(SAMPLE_RATE * dur_s)
    dt = 1/SAMPLE_RATE

    phase = 0 # in range [0, 1)

    for i in range(sample_n):
        t = i*dt
        f = clamp(t_f_func(t), 20, 20000)
        phase += dt*f  # T = 1/f; dt/T
        phase %= 1
        y = vol*sin(tau*phase)
        yield y

def jirj(fs: list[float], dur_s: float, *, vol: float = 1) -> Iterator[float]:
    """switches between frequency `fs[0]`, then `fs[1]`, etc"""
    sample_n = int(SAMPLE_RATE * dur_s)
    dt = 1/SAMPLE_RATE

    phase = 0  # in range [0, 1)
    f_it = cycle(fs)
    f = next(f_it)

    for i in range(sample_n):
        y = vol*sin(tau*phase)
        phase += dt*f  # T = 1/f; dt/T
        if phase >= 1:
            f = next(f_it)
            phase %= 1
        yield y