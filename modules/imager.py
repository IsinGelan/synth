
from itertools import islice
from typing import Iterator

from PIL import Image

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

def display_fft_res(fft_res: list[complex]):
    w, h = 500, 300
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

    
