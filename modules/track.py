
from abc import ABC
from dataclasses import dataclass
from itertools import zip_longest
from typing import Callable, Iterable, Iterator, Self

from .helpers import clamp, int_to_interval, interval_to_int

# Wie yield in FUnktionen implementieren?

class Track(ABC):
    """Abstract base class for Tracks"""
    def __init__(self, sample_rate: int = 48000) -> None:
        self.sample_rate = sample_rate
        self.dur = 0

    def __iter__(self):
        ...


class IterationObject(ABC):
    @property
    def typus(self) -> str:
        return self.__class__.__name__


@dataclass
class Parts(IterationObject):
    parts: list[Track]
    _part_iter = None

    def then(self, track: Track) -> None:
        assert track is not None
        self.parts.append(track)
    
    # ==================
    def _stop_if_empty(self):
        if len(self.parts):
            return
        # was ist, wenn __iter__ aufgerufen wird, aber _part_iter nicht leer ist?
        raise StopIteration("Parts object is empty!")

    def __iter__(self):
        if not len(self.parts):
            self._part_iter = iter([])
        else:
            first_part = self.parts.pop(0)
            self._part_iter = iter(first_part)
        return self
    
    def __next__(self) -> float:
        try:
            return next(self._part_iter)
        except StopIteration:
            self._stop_if_empty()
            first_part = self.parts.pop(0)
            self._part_iter = iter(first_part)
            return next(self)

iteration = 0

@dataclass
class Addition(IterationObject):
    parts: list[Track]
    _to_be_removed = []

    def add(self, track: Track):
        """vielleicht später noch Gewichtung hinzufügen
        (oder auch nicht, man kann ja auch vorher die Lautstärke anpassen)"""
        self.parts.append(track)
    
    # ==================    
    def _stop_if_empty(self):
        if len(self.parts):
            return
        # was ist, wenn __iter__ aufgerufen wird, aber _part_iter nicht leer ist?
        raise StopIteration("Parts object is empty!")
    
    def __iter__(self):
        for part in self.parts:
            iter(part)
        return self
    
    def _res_from(self, part: Track) -> float:
        try:
            return next(part)
        except StopIteration:
            self._to_be_removed.append(part)
            return 0
        
    def _remove_stopped_parts(self):
        for part in self._to_be_removed:
            self.parts.remove(part)
        self._to_be_removed = []
    
    def __next__(self) -> float:
        self._stop_if_empty()

        res = sum(self._res_from(part) for part in self.parts)
        self._remove_stopped_parts()

        return res


@dataclass
class Multiply(IterationObject):
    track: Track | IterationObject
    factor: float

    # ==================    
    def __iter__(self):
        iter(self.track)
        return self
    
    def __next__(self):
        ret = next(self.track) * self.factor
        return clamp(ret, -1, 1)


@dataclass
class MultiplyFunction(IterationObject):
    """factor_fun: (t) -> [-1, 1]"""
    track: Track
    factor_fun: Callable[[float], float]
    sample_rate: int = 48000
    _time = 0
    _dt = 0

    # ==================    
    def __iter__(self):
        iter(self.track)
        self._dt = 1 / self.sample_rate
        return self
    
    def __next__(self) -> float:
        factor = self.factor_fun(self._time)
        self._time += self._dt
        ret = next(self.track) * factor
        return clamp(ret, -1, 1)


@dataclass
class FromIterator(IterationObject):
    """Intermediate object, so that MonoTracks can source from Iterators"""
    it: Iterator

    def __iter__(self):
        return self

    def __next__(self) -> float:
        return next(self.it)


@dataclass
class FromList(IterationObject):
    lis: list
    _iterator = None

    def __iter__(self):
        self._iterator = iter(self.lis)
        return self

    def __next__(self) -> float:
        return next(self._iterator)

class MonoTrack(Track):
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.obj: IterationObject = Parts([])
        self._iterator = None
    
    @classmethod
    def from_obj(cls, obj: IterationObject, sample_rate: int = 48000) -> Self:
        mtr = cls(sample_rate)
        mtr.obj = obj
        return mtr

    @classmethod
    def from_iter(cls, iterator: Iterator[float], sample_rate: int = 48000) -> Self:
        return cls.from_obj(FromIterator(iterator), sample_rate)
    
    @classmethod
    def from_list(cls, lis: list[float], sample_rate: int = 48000) -> Self:
        return cls.from_obj(FromList(lis), sample_rate)
    
    @classmethod
    def from_audio_blocs(cls, int_blocs: list[tuple[int]], *, channel_index: int, sample_rate: int = 48000) -> Self:
        it = (int_to_interval(bloc[channel_index]) for bloc in int_blocs)
        return cls.from_iter(it, sample_rate)
    
    # ==================
    def asdr(self, a: float, d: float, s: float, r: float, *, hit_time: float) -> Self:
        def asdr_fun(t: float):
            if t < a:
                return t/a
            if t < a+d:
                x = (t-a)/d
                return 1 - x*(1-s)
            if t < hit_time:
                return s
            if t < hit_time + r:
                x = (t-hit_time)/r
                return (1-x)*s
            return 0

        return self.mul_func(asdr_fun)

    def then(self, other: Self) -> Self:
        if self.obj.typus == "Parts":
            self.obj.then(other)
        else:
            new_obj = Parts([self.obj])
            new_obj.then(other)
            self.obj = new_obj
        return self

    def then_iter(self, iterator: Iterator[float], sample_rate = 48000) -> Self:
        mtr = MonoTrack.from_iter(iterator, sample_rate)
        return self.then(mtr)

    def add(self, other: Self) -> Self:
        if self.obj.typus == "Addition":
            self.obj.add(other)
        else:
            new_obj = Addition([self.obj, other])
            self.obj = new_obj
        return self
    
    def mul(self, factor: float) -> Self:
        """multiplies the volume of the track"""
        if self.obj.typus == "Multiply":
            self.obj.factor *= factor
        else:
            self.obj = Multiply(self.obj, factor)
        return self

    def mul_func(self, factor_fun: Callable[[float], float]) -> Self:
        self.obj = MultiplyFunction(self.obj, factor_fun, sample_rate=self.sample_rate)
        return self
    
    def copy(self) -> Self:
        cop = MonoTrack(self.sample_rate)
        cop.obj = self.obj
        return cop
    
    # ==================
    def __iter__(self):
        self._iterator = iter(self.obj)
        return self
    
    def __next__(self) -> float:
        return next(self._iterator)


class FrozenMonoTrack(Track):
    """In this case, the track is not a dynamic iterator, but already fully known.\n
    helpful for multiple use, for example for a snippet of audio"""
    def __init__(self, track: MonoTrack, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.track = list(track)
        self.dur = len(self.track) / sample_rate

    @classmethod
    def from_iter(cls, iterator: Iterator[float], sample_rate: int = 48000) -> Self:
        # return cls.from_obj(FromIterator(iterator), sample_rate)
        pass

    def __iter__(self):
        return iter(self.track)



# Decorator ============
def to_mono_track(fun: Callable[..., Iterator[float]]) -> Callable[..., MonoTrack]:
    """Generates a track from a generator function"""
    def wrapper(*args, **kwargs):
        mtr = MonoTrack()
        it_obj = FromIterator(fun(*args, **kwargs))
        mtr.obj = it_obj
        return mtr
    return wrapper


# PolyTrack ============
ListPolyInt = list[tuple[int]]

class PolyTrack:
    """Für mehrspuriges Audio\n
    soll später auch Unterklasse von Track werden;\n
    `add` und `then` könnte dann aber nur mit gleich breitem Polytrack operieren"""
    def __init__(self, mono_channels: list[MonoTrack]) -> None:
        self.it_of_channels: Iterator[tuple[float]] = zip(*mono_channels)
        self.n = len(mono_channels)
    
    @classmethod
    def multiply_mono(cls, channel: MonoTrack, n: int) -> Self:
        # Funktioniert wohlmöglich nicht
        ptr = cls([])
        ptr.it_of_channels = ((sample,)*n for sample in channel)
        ptr.n = n
        return ptr
    
    def from_audio_blocs(cls, int_blocs: list[tuple[int]], *, channel_n: int) -> Self:
        ptr = cls([])
        ptr.n = channel_n
        ptr.it_of_channels = (
            tuple(int_to_interval(int_sample)
            for int_sample in bloc) for bloc in int_blocs
        )
        return ptr
    
    def to_audio_blocs(self) -> ListPolyInt:
        return [
            tuple(interval_to_int(sample) for sample in poly_sample)
            for poly_sample in self.it_of_channels
        ]
    
