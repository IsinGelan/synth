
from math import sin, tau

from modules.helpers import int_to_interval
from modules.sound_generator import Note, evolving_frequency, jirj, multi_sine, note_str_to_freqs, note_to_freq, silence, triang
from modules.track import MonoTrack, PolyTrack, iteration
from modules.wav_rw import AudioData, read_wav_data, write_wav_data
from modules.fun import display_amplitudes_img

def main():
    audio_data = read_wav_data("suslow_piano.wav")
    sample_dur = 1 / audio_data.sample_rate

    left_piano_track = MonoTrack.from_audio_blocs(audio_data.blocs, channel_index=0).mul(-1.3)

    updown_f = 1.5
    f_fun = lambda t: 400 + 200 * sin(2*tau*updown_f*t) / updown_f
    upidupi_track = MonoTrack.from_iter(evolving_frequency(f_fun, 10, 1.)).mul(0.1)

    print("Sample Rate:", audio_data.sample_rate, "Hz")
    print("Playtime:", audio_data.bloc_n*sample_dur, "s")

    stereo = PolyTrack([left_piano_track, upidupi_track])
    new_audio = AudioData.from_track(stereo)
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
    db = lambda decibels: 10**(decibels/10)
    notes = note_str_to_freqs("dis3 dis6 dis5 ais6 g5 dis7 g6 fis6 c6 d7")
    vols = [db(7), db(0), db(-6), db(-13), db(-16), db(-17), db(-23), db(-25), db(-26), db(-28)]
    it = multi_sine(notes, 4.0, vols=vols)
    mono = MonoTrack.from_iter(it).mul(0.9)

    audio = AudioData.from_track(mono)
    write_wav_data("flute_try.wav", audio)
    
main_flute()
