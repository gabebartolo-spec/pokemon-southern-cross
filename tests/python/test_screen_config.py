"""Screen config (D-017): 480x320 internal resolution, window at 2x, integer scaling, no smoothing."""
import json
import re
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.rmxp import marshal  # noqa: E402

MKXP = ROOT / "game" / "mkxp.json"
PLUGINS = ROOT / "game" / "Plugins"
SCREEN_PLUGIN = PLUGINS / "PSC_Screen"
PLUGIN_SCRIPTS = ROOT / "game" / "Data" / "PluginScripts.rxdata"


def strip_json_comments(text):
    """Drop // and /* */ comments outside strings, then trailing commas (mkxp-z accepts both)."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            out.append(c)
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        else:
            out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_mkxp():
    return json.loads(strip_json_comments(MKXP.read_text(encoding="utf-8")))


def test_strip_json_comments_keeps_slashes_in_strings():
    text = '// head\n{\n  // "x": 1,\n  "url": "https://a/b", /* c */ "n": 2,\n}\n'
    assert json.loads(strip_json_comments(text)) == {"url": "https://a/b", "n": 2}


def test_mkxp_json_integer_scaling():
    cfg = load_mkxp()
    assert cfg["defScreenW"] == 960
    assert cfg["defScreenH"] == 640
    assert cfg["integerScalingActive"] is True
    assert cfg["integerScalingLastMile"] is False
    assert cfg["smoothScaling"] is False
    assert cfg["lanczos3Scaling"] is False
    assert cfg["fixedAspectRatio"] is True


# --- PSC_Screen plugin: 480x320 resolution, and its compiled copy is current ---------------

def _text(raw):
    return raw.raw if hasattr(raw, "raw") else raw


def _meta_name(meta_txt):
    for line in meta_txt.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip().lower() == "name":
            return value.strip()
    return None


def test_screen_plugin_sets_480x320():
    src = (SCREEN_PLUGIN / "screen.rb").read_text(encoding="utf-8")
    assert re.search(r"^\s*WIDTH\s*=\s*480\b", src, re.M)
    assert re.search(r"^\s*HEIGHT\s*=\s*320\b", src, re.M)
    assert "redefine(Settings, :SCREEN_WIDTH, PSC::Screen::WIDTH)" in src
    assert "redefine(Settings, :SCREEN_HEIGHT, PSC::Screen::HEIGHT)" in src
    assert _meta_name(SCREEN_PLUGIN / "meta.txt") == "PSC Screen"


def test_screen_rb_loads_before_the_screen_fixes():
    # Essentials loads a plugin's scripts alphabetically; the ui_*.rb files use PSC::Screen.
    rbs = sorted(p.name for p in SCREEN_PLUGIN.glob("*.rb"))
    assert rbs[0] == "screen.rb"


def test_plugin_scripts_rxdata_matches_plugin_sources():
    # Only debug runs recompile plugins, so a release build runs Data/PluginScripts.rxdata
    # as committed: it must hold exactly the plugins in game/Plugins, with their current code.
    compiled = {}
    for name, _meta, scripts in marshal.loads(PLUGIN_SCRIPTS.read_bytes()):
        compiled[_text(name).decode("utf-8")] = {
            _text(f).decode("utf-8"): zlib.decompress(_text(code)) for f, code in scripts
        }
    sources = {}
    for meta in PLUGINS.glob("*/meta.txt"):
        files = {p.relative_to(meta.parent).as_posix(): p.read_bytes() for p in meta.parent.rglob("*.rb")}
        sources[_meta_name(meta)] = files
    assert sorted(compiled) == sorted(sources)
    for name, files in sources.items():
        assert sorted(compiled[name]) == sorted(files), name
        for f, data in files.items():
            assert compiled[name][f].replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n"), f"{name}/{f} is stale"


def _ruby_int_consts(src):
    return {k: int(v) for k, v in re.findall(r"^\s*([A-Z_0-9]+)\s*=\s*(\d+)\s*$", src, re.M)}


def test_screen_size_option_offers_only_1x_2x_3x_and_fullscreen():
    # Ruling 2026-10-19: Screen Size offers 1x, 2x, 3x and Full; anything else becomes 2x.
    src = (SCREEN_PLUGIN / "screen_size.rb").read_text(encoding="utf-8")
    c = _ruby_int_consts(src)
    scale = lambda size: (size + 1) * 0.5  # Essentials: window scale = (screensize + 1) / 2
    assert [scale(c["SIZE_1X"]), scale(c["SIZE_2X"]), scale(c["SIZE_3X"])] == [1.0, 2.0, 3.0]
    assert c["SIZE_FULL"] == 4  # Essentials' fullscreen value
    sizes = re.search(r"SIZES\s*=\s*\[([^\]]*)\]", src).group(1).split(",")
    assert [s.strip() for s in sizes] == ["SIZE_1X", "SIZE_2X", "SIZE_3X", "SIZE_FULL"]
    assert re.search(r"DEFAULT_SIZE\s*=\s*SIZE_2X\b", src)
    labels = re.search(r'"parameters"\s*=>\s*\[(.*?)\]', src).group(1)
    assert re.findall(r'_INTL\("([^"]+)"\)', labels) == ["1x", "2x", "3x", "Full"]
    assert 'MenuHandlers.add(:options_menu, :screen_size' in src


def test_default_screen_size_is_2x():
    # PokemonSystem's default screensize is (SCREEN_SCALE * 2).floor - 1; it must equal SIZE_2X.
    scale = float(re.search(r"^\s*SCALE\s*=\s*([\d.]+)", (SCREEN_PLUGIN / "screen.rb").read_text(), re.M).group(1))
    size_2x = _ruby_int_consts((SCREEN_PLUGIN / "screen_size.rb").read_text(encoding="utf-8"))["SIZE_2X"]
    assert int(scale * 2) - 1 == size_2x
