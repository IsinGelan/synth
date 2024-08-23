
from math import sin, tau

from modules.helpers import int_to_interval
from modules.sound_generator import Note, evolving_frequency, multiple_frequencies, note_str_to_freqs, note_to_freq, silence
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
        chord_track = MonoTrack.from_iter(multiple_frequencies(freqs, 2.5)).asdr(0.1, 0.7, 0.3, 0.5, hit_time=1.8)
        chord_prog.add(MonoTrack.from_iter(silence(2.0 * i)).then(chord_track))
    chord_prog.mul(0.7)

    audio = AudioData.from_track(chord_prog)
    write_wav_data("chord.wav", audio)
    
    
main2()
