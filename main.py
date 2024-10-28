
from math import cos, log10, pi, sin, tau

from modules.helpers import forward_function
from modules.sound_generator import (
    Note,
    evolving_frequency,
    multi_sine,
    multi_wave,
    note_str_to_freqs,
    sine_with_harmonics,
)
from modules.sound_generator import (
    SAWTOOTH_WAVE,
    SQUARE_WAVE,
    TRIANG_WAVE
)
from modules.track import FrozenMonoTrack, MonoTrack, PolyTrack
from modules.wav_rw import AudioData, read_wav_data, write_wav_data
from modules.imager import display_amplitudes_img

def main_timely():
    fun = forward_function(
        [
            lambda x: x**0.5 * (1-x),
            lambda x: 1/pi * sin(pi*x),
            lambda x: x - 2,
            lambda x: -sin(6*pi*x)/(6*pi) - (x-7/2)**2 / 6 + 3/2,
            lambda x: 0 
        ],
        [1, 2, 7/2, 13/2]
    )
    vfun = forward_function(
        [
            lambda x: 1,
            lambda x: 1-(x-2)/2,
            lambda x: 1/2,
            lambda x: 1/2 + (x-5)/2,
            lambda x: 1
        ],
        [2, 3, 5, 6]
    )
    f_fun = lambda t: 300*fun(t) + 200
    freq_it = evolving_frequency(f_fun, 7.5)
    upidupi_track = MonoTrack.from_iter(freq_it).mul(0.8).mul_func(vfun)

    new_audio = upidupi_track.to_audio()
    write_wav_data("neu_chilly.wav", new_audio)

def main_progression():
    I = "c e g"
    V = "g h e4"
    iv = "a c e"
    IV = "f a c4"

    chord_prog = MonoTrack()
    for i, chord in enumerate([I, V, iv, IV]):
        freqs = note_str_to_freqs(chord)
        print(freqs)
        chord_track = MonoTrack.from_iter(multi_sine(freqs, 2.5))
        chord_track.adsr(0.1, 0.7, 0.3, 0.5, hit_time=1.8)
        chord_prog.add(chord_track, offset_t=1.8*i)
    chord_prog.mul(0.7)

    audio = chord_prog.to_audio()
    write_wav_data("generated/chord.wav", audio)

def main_flute():
    # base = 2**(1/3)
    db = lambda decibels: 10**(decibels/20)
    # notes = note_str_to_freqs("F6 F5 C7 Gis5 F4 Gis6 F7 D6 D7 Ais6 Ais5")
    # vols = list(map(db, [-5, -12, -15, -16, -18, -21, -27, -28, -35, -34, -40]))
    notes = note_str_to_freqs("F2 F3 Cis4 F5 Ais6")
    vols = list(map(db, [-2, -12, -4, -16, -24]))
    it = multi_sine(notes, 4.0, vols=vols)
    mono = MonoTrack.from_iter(it).mul(0.5)

    audio = mono.to_audio()
    # audio.play()
    audio.save("generated/flutn_try.wav")

def main_test():
    wave = multi_wave(SAWTOOTH_WAVE, note_str_to_freqs("C E G"), 4.0)
    track = MonoTrack.from_iter(wave).mul(0.7)
    audio = track.to_audio()
    write_wav_data("test.wav", audio)

def main_harmonics():
    num_of_harmonics = 8
    vol_fun = lambda x: cos(x) * (1/x + 0.2)
    wave = sine_with_harmonics(note_str_to_freqs("C2")[0], num_of_harmonics, vol_fun, dur_s=4)
    track = MonoTrack.from_iter(wave).mul(1/200)
    audio = track.to_audio()
    audio.play()
    audio.save("generated/timbre.wav")

def main_harmonics2():
    db_to_p = lambda db: 2**(db/10)
    fundamental = 220

    # OBOE
    fs = [fundamental*i for i in range(1, 6)]
    db_vols = [0, 12, 7, 17, -5]
    vol_mul = 0.3
    # PIANO (not good)
    # fs = [fundamental*i for i in range(1, 9)]
    # # db_vols = [0, -12, -9, -17, -23]
    # vols = [0.226, 0.057, 0.077, 0.033, 0.015, 0.011, 0.007, 0.009]
    # vol_mul = 0.9
    # VIOLIN (not good)
    # fs = [fundamental*i for i in range(1, 6, 1)]
    # db_vols = [0, -5, -4, -12, -13]
    # vol_mul = 0.4

    # ---
    vols = [db_to_p(v) for v in db_vols]
    wave = multi_sine(fs, 2.0, vols=vols)
    track = MonoTrack.from_iter(wave).mul(vol_mul)
    audio = track.to_audio()
    audio.play()
    audio.save("generated/oboe.wav")

main_progression()
