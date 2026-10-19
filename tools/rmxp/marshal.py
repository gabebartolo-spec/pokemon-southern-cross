"""Ruby Marshal 4.8 reader and writer, standard library only.

Import as ``tools.rmxp.marshal`` (it shadows the stdlib module only inside this package).
Round trips are byte for byte: object links (@) and symbol links (;) are reproduced by
object identity, string encoding ivars are kept, floats and bignums keep their original bytes.

Writing: Ruby Strings must be ``RString`` (``RString.utf8("text")`` for new UTF-8 text) and
Symbols ``Sym``; a plain Python ``str`` is rejected by ``dumps``. Give every String its own
RString object: one object written twice becomes a Ruby object link.
"""


class Sym(str):
    """A Ruby Symbol (a str subclass so it differs from a String)."""
    __slots__ = ()


class RString:
    """A Ruby String: raw bytes plus the ordered ivars (encoding etc.) as (name, value) pairs."""
    __slots__ = ("raw", "ivars")

    def __init__(self, raw=b"", ivars=None):
        self.raw = raw
        self.ivars = ivars if ivars is not None else []

    def __eq__(self, other):
        return isinstance(other, RString) and self.raw == other.raw and self.ivars == other.ivars

    def __hash__(self):
        return hash(self.raw)

    def __repr__(self):
        return "RString(%r)" % (self.raw,)

    @property
    def text(self):
        return self.raw.decode("utf-8", "replace")

    @classmethod
    def utf8(cls, s):
        return cls(s.encode("utf-8"), [("E", True)])


class RFloat(float):
    """A Float that remembers its original byte text in ``raw``."""
    raw = None


class RBignum(int):
    """An Integer outside the Fixnum range; ``raw`` is (sign byte, magnitude bytes) as read."""
    raw = None


class RubyObject:
    """A Ruby object ('o'): class name and ordered ivars (names include the @)."""

    def __init__(self, cls, ivars=None):
        self.cls = cls
        self.ivars = ivars if ivars is not None else {}

    def __repr__(self):
        return "RubyObject(%s, %d ivars)" % (self.cls, len(self.ivars))


class UserDef:
    """A user-dumped object ('u', _dump): Table, Color, Tone. ivars is None unless 'I' wrapped."""

    def __init__(self, cls, raw, ivars=None):
        self.cls = cls
        self.raw = raw
        self.ivars = ivars

    def __repr__(self):
        return "UserDef(%s, %d bytes)" % (self.cls, len(self.raw))


class RHash(dict):
    """A Ruby Hash; ``default`` holds the default value of a '}' hash."""
    has_default = False
    default = None


class MarshalError(Exception):
    pass


FIXNUM_MIN, FIXNUM_MAX = -(1 << 30), (1 << 30) - 1


# ---------------------------------------------------------------- reading

class _Reader:
    def __init__(self, data):
        self.d = data
        self.p = 2
        self.syms = []
        self.objs = []

    def byte(self):
        if self.p >= len(self.d):
            raise MarshalError("truncated data")
        b = self.d[self.p]
        self.p += 1
        return b

    def take(self, n):
        if n < 0 or self.p + n > len(self.d):
            raise MarshalError("truncated data")
        s = self.d[self.p:self.p + n]
        self.p += n
        return s

    def long(self):
        c = self.byte()
        if c > 127:
            c -= 256
        if c == 0:
            return 0
        if 4 < c < 128:
            return c - 5
        if -129 < c < -4:
            return c + 5
        if c > 0:
            x = 0
            for i in range(c):
                x |= self.byte() << (8 * i)
            return x
        x = -1
        for i in range(-c):
            x &= ~(0xFF << (8 * i))
            x |= self.byte() << (8 * i)
        return x

    def bytestr(self):
        return self.take(self.long())

    def _newsym(self):
        s = Sym(self.bytestr().decode("utf-8"))
        self.syms.append(s)
        return s

    def symbol(self):
        t = self.byte()
        if t == 0x3A:
            return self._newsym()
        if t == 0x3B:
            return self.syms[self.long()]
        raise MarshalError("expected symbol at %d" % (self.p - 1))

    def ivar_list(self):
        out = []
        for _ in range(self.long()):
            k = str(self.symbol())
            out.append((k, self.obj()))
        return out

    def userdef(self):
        name = str(self.symbol())
        u = UserDef(name, self.bytestr())
        self.objs.append(u)
        return u

    def obj(self):
        c = chr(self.byte())
        if c == "0":
            return None
        if c == "T":
            return True
        if c == "F":
            return False
        if c == "i":
            return self.long()
        if c == ":":
            return self._newsym()
        if c == ";":
            return self.syms[self.long()]
        if c == "@":
            return self.objs[self.long()]
        if c == "I":
            inner = chr(self.byte())
            if inner == '"':
                s = RString(self.bytestr())
                self.objs.append(s)
                s.ivars = self.ivar_list()
                return s
            if inner == "u":
                u = self.userdef()
                u.ivars = self.ivar_list()
                return u
            raise MarshalError("ivars on type %r unsupported" % inner)
        if c == '"':
            s = RString(self.bytestr())
            self.objs.append(s)
            return s
        if c == "f":
            raw = self.bytestr()
            txt = raw.decode("ascii")
            f = RFloat(float(txt.split("\0")[0]))
            f.raw = raw
            self.objs.append(f)
            return f
        if c == "l":
            sign = self.byte()
            raw = self.take(self.long() * 2)
            v = int.from_bytes(raw, "little")
            b = RBignum(-v if sign == 0x2D else v)
            b.raw = (sign, raw)
            self.objs.append(b)
            return b
        if c == "[":
            a = []
            self.objs.append(a)
            for _ in range(self.long()):
                a.append(self.obj())
            return a
        if c in "{}":
            h = RHash()
            self.objs.append(h)
            for _ in range(self.long()):
                k = self.obj()
                h[k] = self.obj()
            if c == "}":
                h.has_default = True
                h.default = self.obj()
            return h
        if c == "o":
            o = RubyObject(str(self.symbol()))
            self.objs.append(o)
            for _ in range(self.long()):
                k = str(self.symbol())
                o.ivars[k] = self.obj()
            return o
        if c == "u":
            return self.userdef()
        raise MarshalError("unsupported type %r at %d" % (c, self.p - 1))


def loads(data):
    data = bytes(data)
    if data[:2] != b"\x04\x08":
        raise MarshalError("not Marshal 4.8 data")
    r = _Reader(data)
    v = r.obj()
    if r.p != len(data):
        raise MarshalError("trailing bytes after object")
    return v


# ---------------------------------------------------------------- writing

class _Writer:
    def __init__(self):
        self.out = bytearray()
        self.syms = {}
        self.seen = {}
        self.keep = []  # keeps objects alive so id() stays unique

    def long(self, n):
        o = self.out
        if n == 0:
            o.append(0)
        elif 0 < n < 123:
            o.append(n + 5)
        elif -124 < n < 0:
            o.append((n - 5) & 0xFF)
        else:
            buf = bytearray()
            x = n
            for i in range(1, 5):
                buf.append(x & 0xFF)
                x >>= 8
                if x == 0:
                    o.append(i)
                    break
                if x == -1:
                    o.append((-i) & 0xFF)
                    break
            o.extend(buf)

    def bytestr(self, b):
        self.long(len(b))
        self.out.extend(b)

    def symbol(self, s):
        s = str(s)
        if s in self.syms:
            self.out.append(0x3B)
            self.long(self.syms[s])
        else:
            self.syms[s] = len(self.syms)
            self.out.append(0x3A)
            self.bytestr(s.encode("utf-8"))

    def linked(self, o):
        """Emit a link and return True if o was already written; else register it."""
        i = self.seen.get(id(o))
        if i is not None:
            self.out.append(0x40)
            self.long(i)
            return True
        self.seen[id(o)] = len(self.seen)
        self.keep.append(o)
        return False

    def ivar_list(self, pairs):
        self.long(len(pairs))
        for k, v in pairs:
            self.symbol(k)
            self.obj(v)

    def obj(self, v):
        o = self.out
        if v is None:
            o.append(0x30)
        elif v is True:
            o.append(0x54)
        elif v is False:
            o.append(0x46)
        elif isinstance(v, Sym):
            self.symbol(v)
        elif isinstance(v, int):
            if isinstance(v, RBignum) or not FIXNUM_MIN <= v <= FIXNUM_MAX:
                if self.linked(v):
                    return
                self.bignum(v)
            else:
                o.append(0x69)
                self.long(int(v))
        elif isinstance(v, float):
            if self.linked(v):
                return
            o.append(0x66)
            raw = getattr(v, "raw", None)
            if raw is None:
                if v != v:
                    raw = b"nan"
                elif v in (float("inf"), float("-inf")):
                    raw = b"inf" if v > 0 else b"-inf"
                else:
                    raw = repr(float(v)).encode("ascii")
                    if raw.endswith(b".0"):
                        raw = raw[:-2]
            self.bytestr(raw)
        elif isinstance(v, RString):
            if self.linked(v):
                return
            if v.ivars:
                o.append(0x49)
            o.append(0x22)
            self.bytestr(v.raw)
            if v.ivars:
                self.ivar_list(v.ivars)
        elif isinstance(v, UserDef):
            if self.linked(v):
                return
            if v.ivars:
                o.append(0x49)
            o.append(0x75)
            self.symbol(v.cls)
            self.bytestr(v.raw)
            if v.ivars:
                self.ivar_list(v.ivars)
        elif isinstance(v, list):
            if self.linked(v):
                return
            o.append(0x5B)
            self.long(len(v))
            for x in v:
                self.obj(x)
        elif isinstance(v, dict):
            if self.linked(v):
                return
            dflt = getattr(v, "has_default", False)
            o.append(0x7D if dflt else 0x7B)
            self.long(len(v))
            for k, x in v.items():
                self.obj(k)
                self.obj(x)
            if dflt:
                self.obj(v.default)
        elif isinstance(v, RubyObject):
            if self.linked(v):
                return
            o.append(0x6F)
            self.symbol(v.cls)
            self.long(len(v.ivars))
            for k, x in v.ivars.items():
                self.symbol(k)
                self.obj(x)
        else:
            raise MarshalError("cannot dump %r" % type(v))

    def bignum(self, v):
        raw = getattr(v, "raw", None)
        if raw is not None:
            sign, body = raw
        else:
            sign = 0x2D if v < 0 else 0x2B
            n = abs(int(v))
            body = n.to_bytes((n.bit_length() + 7) // 8, "little")
            if len(body) % 2:
                body += b"\0"
        self.out.append(0x6C)
        self.out.append(sign)
        self.long(len(body) // 2)
        self.out.extend(body)


def dumps(v):
    w = _Writer()
    w.out.extend(b"\x04\x08")
    w.obj(v)
    return bytes(w.out)
