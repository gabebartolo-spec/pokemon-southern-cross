from pathlib import Path

import pytest

from tools.rmxp import marshal, rpg

DATA = Path(__file__).resolve().parents[2] / "game" / "Data"
FILES = sorted(DATA.glob("Map*.rxdata")) + [DATA / "Tilesets.rxdata"]
FILES = sorted(set(FILES), key=lambda p: p.name)  # MapInfos.rxdata is matched by Map*.rxdata


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_roundtrip_every_base_map(path):
    b = path.read_bytes()
    assert marshal.dumps(marshal.loads(b)) == b


def test_base_file_set_is_complete():
    names = {p.name for p in FILES}
    assert "MapInfos.rxdata" in names and "Tilesets.rxdata" in names
    assert len([n for n in names if n.startswith("Map0")]) >= 60


def test_scalars_and_links_roundtrip():
    shared = marshal.RString.utf8("hi")
    v = [None, True, False, 0, 1, -1, 122, 123, -123, -124, 255, 256, 65536, -65537,
         (1 << 30) - 1, -(1 << 30), 1 << 40, -(1 << 70), 1.5, shared, shared,
         marshal.Sym("a"), marshal.Sym("a"), {marshal.Sym("k"): shared}]
    b = marshal.dumps(v)
    assert marshal.dumps(marshal.loads(b)) == b
    out = marshal.loads(b)
    assert out[19] is out[20] and out[1] is True
    assert out[5] == -1 and out[13] == -65537 and out[-1][marshal.Sym("k")] is out[19]


def test_hash_default_roundtrip():
    h = marshal.RHash()
    h.has_default, h.default = True, 7
    h[1] = 2
    b = marshal.dumps(h)
    assert b.startswith(b"\x04\x08}") and marshal.dumps(marshal.loads(b)) == b


def test_table_roundtrip():
    t = rpg.Table(3, 2, 2, list(range(12)))
    u = t.to_userdef()
    assert len(u.raw) == 20 + 24
    assert rpg.Table.from_userdef(u) == t
    b = marshal.dumps(u)
    assert marshal.dumps(marshal.loads(b)) == b


def test_edit_table_cell_in_loaded_map():
    b = (DATA / "Map001.rxdata").read_bytes()
    m = marshal.loads(b)
    t = rpg.Table.from_userdef(m.ivars["@data"])
    assert t.to_userdef().raw == m.ivars["@data"].raw
    old = t.get(2, 3, 1)
    t.set(2, 3, 1, 1234)
    m.ivars["@data"] = t.to_userdef()
    m2 = marshal.loads(marshal.dumps(m))
    t2 = rpg.Table.from_userdef(m2.ivars["@data"])
    assert t2.get(2, 3, 1) == 1234 and old != 1234
    t2.set(2, 3, 1, old)
    m2.ivars["@data"] = t2.to_userdef()
    assert marshal.dumps(m2) == b
