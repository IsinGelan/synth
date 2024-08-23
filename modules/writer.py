from typing import Iterator


class Writer:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.file_obj = None

    def __enter__(self):
        self.file_obj = open(self.filename, "wb")
        return self

    def __exit__(self, typus, value, traceback):
        if traceback:
            raise value
        assert self.file_obj is not None
        self.file_obj.close()
        return True

    def write_chars(self, chars: str):
        assert self.file_obj
        self.file_obj.write(chars.encode())

    def write_byte(self, by: int):
        assert self.file_obj
        buffer = bytes([by])
        self.file_obj.write(buffer)

    def write_bytes(self, bys: bytes):
        assert self.file_obj
        self.file_obj.write(bys)

    def write_iterator(self, it: Iterator[int]):
        for by in it:
            self.write_byte(by)

    def write_uint16(self, num: int):
        """Little endian"""
        self.write_bytes(num.to_bytes(2, "little"))

    def write_uint32(self, num: int):
        """Little endian"""
        self.write_bytes(num.to_bytes(4, "little"))
    
