
from math import pi, sin, tau

from modules.helpers import forward_function, int_to_interval
from modules.sound_generator import (
    Note,
    evolving_frequency,
    multi_sine,
    multi_wave,
    note_str_to_freqs,
    note_to_freq,
    silence,
    triang
)
from modules.sound_generator import (
    SAWTOOTH_WAVE,
    SQUARE_WAVE,
    TRIANG_WAVE
)
from modules.track import MonoTrack, PolyTrack
from modules.wav_rw import AudioData, read_wav_data, write_wav_data
from modules.fun import display_amplitudes_img

def main():
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

    new_audio = AudioData.from_track(upidupi_track)
    write_wav_data("neu_chilly.wav", new_audio)

def main2():
    I = "c e g"
    V = "g h e4"
    iv = "a c e"
    IV = "f a c4"

    chord_prog = MonoTrack()
    for i, chord in enumerate([I, V, iv, IV]):
        freqs = note_str_to_freqs(chord)
        chord_track = MonoTrack.from_iter(multi_sine(freqs, 2.5))
        chord_track.adsr(0.1, 0.7, 0.3, 0.5, hit_time=1.8)
        chord_prog.add(MonoTrack.from_iter(silence(2.0 * i)).then(chord_track))
    chord_prog.mul(0.7)

    audio = AudioData.from_track(chord_prog)
    write_wav_data("chord.wav", audio)

def main3():
    # freqs = note_str_to_freqs("c e g")
    # mono = MonoTrack.from_iter(jirj(freqs, 3.)).adsr(0.1, 0.7, 0.3, 0.7, hit_time=2.).mul(0.7)
    mono = MonoTrack.from_iter(triang(note_to_freq(Note.C, 4), 4.0))
    mono2 = MonoTrack.from_iter(triang(note_to_freq(Note.E, 4), 4.0))
    audio = AudioData.from_track(mono.add(mono2).mul(0.3))
    write_wav_data("jirj.wav", audio)

def main_flute():
    # base = 2**(1/3)
    db = lambda decibels: 10**(decibels/20)
    # notes = note_str_to_freqs("F6 F5 C7 Gis5 F4 Gis6 F7 D6 D7 Ais6 Ais5")
    # vols = list(map(db, [-5, -12, -15, -16, -18, -21, -27, -28, -35, -34, -40]))
    notes = note_str_to_freqs("F2 F3 Cis4 F5 Ais6")
    vols = list(map(db, [-2, -12, -4, -16, -24]))
    it = multi_sine(notes, 4.0, vols=vols)
    mono = MonoTrack.from_iter(it).mul(0.5)

    audio = AudioData.from_track(mono)
    write_wav_data("flute_try.wav", audio)

def main_test():
    wave = multi_wave(SAWTOOTH_WAVE, note_str_to_freqs("C E G"), 4.0)
    track = MonoTrack.from_iter(wave).mul(0.7)
    audio = AudioData.from_track(track)
    write_wav_data("test.wav", audio)
    
main_test()
