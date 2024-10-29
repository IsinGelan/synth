
from itertools import islice
from typing import Iterator
from scipy.fft import fft
from scipy.signal.windows import blackman

from .helpers import windowed
from .track import FrozenMonoTrack, MonoTrack


def fft_full(snippet: FrozenMonoTrack) -> list[float]:
    """FFT on the snippet (from 0 to 24000 Hz)\n
    freq.res = `1/dur Hz` (where dur is the duration of the snippet, assuming SR of 24000) \n
    iow. generates 1 data point for every data point in the snippet\n
    eg. a 0.2 second snippet has a frequency resolution of 1/0.2 Hz = 5 Hz"""
    res = fft(snippet.track, snippet.sample_n)
    print(snippet.dur, len(res))
    return res[:len(res)//2]

def fft_shorttime(
        track: MonoTrack | FrozenMonoTrack, *,
        times_per_sec: float,
        freq_resolution: float
    ) -> Iterator[list[float]]:
    """freq_resolution: difference between frequencies in neighboring entries\n
    times_per_sec: how many times per second to perform an FFT"""
    dur = 1/freq_resolution * 24000/track.sample_rate
    window_size = int(dur * track.sample_rate)
    window_step = int(track.sample_rate/times_per_sec)
    print(f"{window_size=} {window_step=}")
    return (fft(win, window_size) for win in windowed(iter(track), window_size, window_step))

def peak_iter(lis: list[float], *, lo_threshold: float) -> Iterator:
    """returns the peaks (the index where they were found, their height) if they are higher than lo_threshold"""
    for i, v in enumerate(lis[1:-1], start=1):
        if v < lo_threshold:
            continue
        if lis[i-1] < v and v > lis[i+1]:
            yield (i, v)

def peaks(lis: list[float], lo_threshold: float) -> dict[int, float]:
    """returns the peaks (the index where they were found, their height) if they are higher than lo_threshold\n
    A peak is a sample with lower samples to both sides."""
    dict(peak_iter(lis, lo_threshold=lo_threshold))

def multiply_with_window(it: Iterator[float], window_size: int) -> Iterator[list[float]]:
    window = blackman(window_size)
    return [[factor* num for factor, num in zip(window, win)] for win in windowed(it, window_size)]
