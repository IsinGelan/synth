
from dataclasses import dataclass
from itertools import islice
from typing import Self

import pyaudio

from .reader import Reader
from .writer import Writer


@dataclass
class AudioData:
    byte_p_sample:  int
    bloc_n:         int
    # Blocs in the respective format (dependent on audio_fmt)
    blocs:  list[tuple]
    audio_fmt:      int = 1
    channels:       int = 2
    sample_rate:    int = 48000
    bit_p_sample:   int = 16

    @classmethod
    def from_blocs(
        cls: Self,
        blocs: list[tuple],
        channels: int = 2,
        sample_rate: int = 48000,
        bit_p_sample: int = 16
    ) -> Self:
        byte_p_sample = ((bit_p_sample + 7) >> 3)
        byte_p_bloc = byte_p_sample * channels
        bloc_n = len(blocs)
        return cls(
            byte_p_sample,
            bloc_n,
            blocs,
            channels=channels,
            sample_rate=sample_rate
        )
    
    @classmethod
    def from_file(cls, filename: str) -> Self:
        return read_wav_data(filename)
    
    def play(self):
        """Plays the audio"""
        bytestream = bytes().join(
            samples_bloc_to_byte_bloc(samples, self.byte_p_sample, self.audio_fmt)
            for samples in self.blocs
        )

        pya = pyaudio.PyAudio()
        stream = pya.open(
            format=pya.get_format_from_width(width=2),
            channels=self.channels,
            rate=self.sample_rate,
            output=True
        )
        stream.write(bytestream)
        stream.stop_stream()
        stream.close()

        pya.terminate()
    
    def save(self, filename: str):
        write_wav_data(filename, self)


def byte_bloc_to_samples_bloc(by_blo: bytes, channels: int, sample_width: int, audio_fmt: int) -> tuple:
    """len(by_blo) == channels * sample_width"""
    if audio_fmt != 1:
        raise NotImplementedError(
            f"audiofmt of {audio_fmt} not implemented yet!")
    byte_samples = [by_blo[i*sample_width: (i+1)*sample_width] for i in range(channels)]
    return tuple(int.from_bytes(sam, "little", signed=True) for sam in byte_samples)


def samples_bloc_to_byte_bloc(samples_bloc: tuple[int], sample_width: int, audio_fmt: int) -> bytes:
    """len(samples_bloc) == channels"""
    if audio_fmt != 1:
        raise NotImplementedError(
            f"audiofmt of {audio_fmt} not implemented yet!")

    byte_samples = [sample.to_bytes(sample_width, "little", signed=True) for sample in samples_bloc]
    return bytes().join(byte_samples)


def read_wav_data(from_filename: str) -> AudioData:
    with Reader(from_filename) as reader:
        # Master RIFF Chunk
        file_type = reader.read_n_chars(4)
        assert file_type == "RIFF"
        file_size = reader.read_uint32()   # number of bytes from here on
        file_fmt = reader.read_n_chars(4)
        assert file_fmt == "WAVE"

        # Data format chunk
        fmt_bloc_id = reader.read_n_chars(4)
        assert fmt_bloc_id == "fmt "
        chunk_size  = reader.read_uint32()   # Größe des übrigen chunks
        audio_fmt   = reader.read_uint16()   # 1: PCM int, 3: IEEE 754
        channels    = reader.read_uint16()
        # in Hz (Samples/Sekunde/Kanal = Blocks/Sekunde)
        sample_rate = reader.read_uint32()
        byte_p_sec  = reader.read_uint32()   # ???
        # (Bytes/Block) (= channels * (bit_p_sample + 7) // 8)
        bloc_width  = reader.read_uint16()
        bit_p_sample = reader.read_uint16()

        # Data chunk
        nextbloc_id = reader.read_n_chars(4)
        if nextbloc_id != "data":
            assert nextbloc_id == "LIST"
            bloc_size = reader.read_uint32()
            reader.skip_n(bloc_size)

            databloc_id = reader.read_n_chars(4)
            assert databloc_id == "data"
        
        data_size   = reader.read_uint32()   # number of bytes in the next section
        bloc_n      = data_size//bloc_width
        byte_p_sample = bloc_width//channels

        # Sampled data
        # # Bloc = [sample_channel0, sample_channel1, ...]
        bloc_it = islice(reader.read_blocks_of_n(bloc_width), bloc_n)
        blocks = [byte_bloc_to_samples_bloc(
            bloc, channels, byte_p_sample, audio_fmt) for bloc in bloc_it]

        return AudioData(
            audio_fmt=audio_fmt,
            channels=channels,
            sample_rate=sample_rate,
            bit_p_sample=bit_p_sample,
            byte_p_sample=byte_p_sample,
            bloc_n=bloc_n,
            blocs=blocks
        )


def write_wav_data(to_filename: str, data: AudioData):
    with Writer(to_filename) as writer:

        bloc_width = data.channels * ((data.bit_p_sample + 7) >> 3)
        byte_p_sec = data.sample_rate * bloc_width
        data_size = data.bloc_n * bloc_width

        # Master RIFF Chunk
        writer.write_chars("RIFF")  # file_type
        writer.write_uint32(data_size + 36)  # number of bytes from here on
        writer.write_chars("WAVE")  # file_fmt

        # Data format chunk
        writer.write_chars("fmt ")
        writer.write_uint32(16)  # chunk_size # Größe des übrigen chunks
        writer.write_uint16(data.audio_fmt)
        writer.write_uint16(data.channels)
        writer.write_uint32(data.sample_rate)
        writer.write_uint32(byte_p_sec)
        writer.write_uint16(bloc_width)
        writer.write_uint16(data.bit_p_sample)

        # Data chunk
        writer.write_chars("data")
        writer.write_uint32(data_size)  # number of bytes in the next section

        # Sampled data
        # # Bloc = [sample_channel0, sample_channel1, ...]
        for samples_bloc in data.blocs:
            byte_bloc = samples_bloc_to_byte_bloc(
                samples_bloc,
                data.byte_p_sample,
                data.audio_fmt
            )
            writer.write_bytes(byte_bloc)
