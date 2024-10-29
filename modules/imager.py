
from itertools import islice
from typing import Iterator

from PIL import Image, ImageDraw

from modules.helpers import clamp, windowed

from .wav_rw import AudioData

def every_n(it: Iterator, n: int) -> Iterator:
    for i, el in enumerate(it):
        if i % n:
            continue
        yield el

def mirror(x, y, h) -> tuple[int, int, int]:
    return (x, h-y)

def display_amplitudes_img(audio_data: AudioData):
    chosing_n = 6000
    chosing_rate = audio_data.bloc_n//chosing_n
    height = 200

    max_possible = 1 << (audio_data.byte_p_sample * 8) >> 1

    img = Image.new("1", (chosing_n, 4*height))

    samples_chosen = islice(every_n(audio_data.blocs, chosing_rate), chosing_n)

    for i, bloc in enumerate(samples_chosen):
        l, r = bloc
        vol = int(l / max_possible * height)
        offset = height - abs(vol)  # if vol >= 0 else height

        for y in range(2*abs(vol)):
            img.putpixel((i, offset+y), 1)

        vol = int(r / max_possible * height)
        offset = height - abs(vol)  # if vol >= 0 else height

        for y in range(2*abs(vol)):
            img.putpixel((i, 2*height+offset+y), 1)

    img.show()

def display_fft_res(fft_res: list[complex], *, wh=(500, 300)):
    w, h = wh
    baseline = 20
    topline = h-20
    leftline = 50
    rightline = w - 50

    innerw, innerh = rightline-leftline, topline-baseline

    top_val = 500
    start, stop = 150, 500

    reslen = len(fft_res)
    choosing_rate = max((stop-start) // innerw, 1)
    it = islice(every_n(fft_res, choosing_rate), start, min(stop, innerw+start))

    img = Image.new("1", (w, h))

    for i, val in enumerate(it):
        val: complex
        for y in range(int(innerh*val.real/top_val)):
            img.putpixel(mirror(leftline+i, baseline+y, h), 1)
        
        img.putpixel(mirror(leftline+i, baseline-5, h), 1)

    img.show()

def stepped_range(start: float, stop: float, step: float) -> Iterator[int]:
    """yields integers"""
    val: float = start
    while val< stop:
        yield int(val)
        val += step

def spectrum_column(
        freq_vol: list[tuple[float, float]],
        output_length: int, *,
        freq_lo: float, freq_hi: float,
        spread_width: float = 5
    ) -> list[float]:
    """spread_width: the delta freq up and down covered by the halo of a frequency\n
    assuming vol data between 0 and 1, but still works fine if not the case"""
    step = (freq_hi - freq_lo) / output_length
    freq_domain = stepped_range(freq_lo, freq_hi, step)
    freqs, vols = zip(*freq_vol)
    freqs_aligned = [int((freq-freq_lo)//step) for freq in freqs]
    spread_steps = int(spread_width / step)
    
    out = [0] * output_length
    for freq_i, vol in zip(freqs_aligned, vols):
        starthalo   = clamp(freq_i - spread_steps, 0, output_length)
        stophalo    = clamp(freq_i + spread_steps, 0, output_length)
        for j in range(starthalo, stophalo):
            dist = abs(j-freq_i) + 1
            val = vol/dist
            out[j] += val

    return out

FFT_ITER = Iterator[list[tuple[float, float]]]

def display_stft(fft_t: FFT_ITER, sample_n: int, wh=(500, 300)):
    """length: number of values to display"""
    w, h = wh
    baseline = 20
    topline = h-20
    leftline = 50
    rightline = w - 50
    innerw, innerh = rightline-leftline, topline-baseline

    img = Image.new("L", (w, h))
    drawer = ImageDraw.Draw(img)

    valit = islice(fft_t, sample_n)

    delta_x = innerw / sample_n
    xit = windowed(stepped_range(0, innerw, delta_x), size=2)

    for val_lis, (x_start, x_end) in zip(valit, xit):
        col = spectrum_column(val_lis, innerh, freq_lo=0, freq_hi=1000, spread_width=10)
        for i, val in enumerate(col, start=baseline):
            val = clamp(val, 0, 1)
            shape = [(leftline + x_start, i), (leftline+x_end-1, i+1)]
            drawer.rectangle(shape, int(val*255))
            
    img.show()

    
