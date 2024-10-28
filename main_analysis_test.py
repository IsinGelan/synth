
from math import log, sqrt

from modules.imager import display_fft_res
from modules.helpers import rescale_values
from modules.sound_analyser import fft_full, peak_iter
from modules.sound_generator import align_to_scale, multi_sine, note_to_freq, sine, note_str_to_freqs
from modules.track import FrozenMonoTrack, MonoTrack, Track
from modules.wav_rw import AudioData


def main():
    filename = "import_sounds/suslow_piano.wav"
    audio = AudioData.from_file(filename)
    track = FrozenMonoTrack.from_audio_data(audio)
    fftres = fft_full(track)

    # with open("outfft.json", "w") as out:
    #     dump(list(float(n) for n in fftres), out, indent="  ")

    display_fft_res(list(fftres))

def main_somesound():
    freqs = note_str_to_freqs("F2 C F A")
    print(freqs)
    track = MonoTrack.from_iter(multi_sine(freqs, 8, vols=[1, 1, 0.5, 2])).mul(0.5)
    track.to_audio().save("generated/buuup.wav")

def main_shifter():
    snippet = FrozenMonoTrack.from_audio_data(
        AudioData.from_file("import_sounds/suslow_piano.wav"))

    freq_vols = [sqrt(v.real**2 + v.imag**2) for v in fft_full(snippet)]
    freq_vols = rescale_values(freq_vols, lo=0, hi=1)

    peaks = [(f / snippet.dur, v) for f, v in peak_iter(freq_vols, lo_threshold=0.05)]
    print(*peaks, sep="\n")


    f, v = tuple(zip(*peaks))
    # f = [note_to_freq(*align_to_scale(freq)) for freq in f]
    
    # import matplotlib.pyplot as plt
    # plt.plot(f, v)
    # plt.show()

    newtrack = MonoTrack.from_iter(multi_sine(f, 3, vols=v))
    newtrack.to_audio().save("generated/newbuuup.wav")

main_shifter()