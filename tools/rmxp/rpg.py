"""RPG Maker XP data classes built on tools.rmxp.marshal."""
import struct

from tools.rmxp.marshal import UserDef


class Table:
    """RPG::Table-style Table: ``<5 x int32 LE: dim, x, y, z, count><int16 LE data>``.

    Data is stored x-fastest: index = x + y * xsize + z * xsize * ysize.
    """

    def __init__(self, xsize, ysize=1, zsize=1, data=None, dim=None):
        self.xsize, self.ysize, self.zsize = xsize, ysize, zsize
        if dim is None:
            dim = 1 if (ysize == 1 and zsize == 1) else (2 if zsize == 1 else 3)
        self.dim = dim
        self.data = list(data) if data is not None else [0] * (xsize * ysize * zsize)
        if len(self.data) != xsize * ysize * zsize:
            raise ValueError("Table data length does not match its size")

    def index(self, x, y=0, z=0):
        return x + y * self.xsize + z * self.xsize * self.ysize

    def get(self, x, y=0, z=0):
        return self.data[self.index(x, y, z)]

    def set(self, x, y, z, value):
        self.data[self.index(x, y, z)] = value

    def to_userdef(self):
        n = len(self.data)
        raw = struct.pack("<5i", self.dim, self.xsize, self.ysize, self.zsize, n)
        raw += struct.pack("<%dh" % n, *self.data)
        return UserDef("Table", raw)

    @classmethod
    def from_userdef(cls, u):
        dim, x, y, z, n = struct.unpack_from("<5i", u.raw, 0)
        if len(u.raw) != 20 + 2 * n or n != x * y * z:
            raise ValueError("malformed Table data")
        return cls(x, y, z, list(struct.unpack_from("<%dh" % n, u.raw, 20)), dim=dim)

    def __eq__(self, other):
        return isinstance(other, Table) and (self.dim, self.xsize, self.ysize, self.zsize, self.data) == \
            (other.dim, other.xsize, other.ysize, other.zsize, other.data)
