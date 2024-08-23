from typing import Iterator


class Reader:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.file_obj = None

    def __enter__(self):
        self.file_obj = open(self.filename, "rb")
        return self

    def __exit__(self, typus, value, traceback):
        if traceback:
            raise value
        assert self.file_obj is not None
        self.file_obj.close()
        return True

    def read_n_chars(self, n: int) -> str:
        assert self.file_obj
        return "".join(chr(x) for x in self.file_obj.read(n))

    def read_byte(self) -> int:
        assert self.file_obj
        return self.file_obj.read(1)[0]
    
    def read_n_bytes(self, n: int) -> bytes:
        assert self.file_obj
        return self.file_obj.read(n)

    def char_iterator(self) -> Iterator[int]:
        # while True:
        #     r = self.file_obj.read(1)
        #     # r like bytes[1]
        #     if r == b"":
        #         break
        #     yield r[0]
        return self.file_obj.read()

    def read_until(self, pattern: str) -> str:
        raise NotImplementedError("read_until is not implmented!")
        for char in self.char_iterator():
            pass

    def read_uint16(self) -> int:
        """Little endian"""
        return int.from_bytes(self.read_n_bytes(2), "little")
        # a, b = self.read_byte(), self.read_byte()
        # return a | b << 8

    def read_uint32(self) -> int:
        """Little endian"""
        return int.from_bytes(self.read_n_bytes(4), "little")
        # a, b, c, d = [self.read_byte() for _ in range(4)]
        # return d << 24 | c << 16 | b << 8 | a

    def read_blocks_of_n(self, n: int) -> Iterator[bytes]:
        while True:
            r = self.file_obj.read(n)
            if len(r) != n:
                print("wrong size:", len(r))
                return
            yield r

    def skip_n(self, n: int):
        assert self.file_obj
        self.file_obj.read(n)
