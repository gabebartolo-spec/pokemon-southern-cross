"""Mega Evolution is the only battle gimmick (D-011).

Neither Essentials v21.1 nor the Generation 9 Pack has a switch for Terastal, Dynamax or Z-Moves:
each comes as its own plugin (the Deluxe Battle Kit add-ons, or older ZUD/Terastal plugins). So
"off" means: no such plugin is installed and no installed script defines those battle options.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS = ROOT / "game" / "Plugins"
GIMMICKS = PLUGINS / "PSC_Gimmicks" / "gimmicks.rb"

# A plugin whose meta.txt Name matches this adds a forbidden gimmick.
GIMMICK_PLUGIN_NAME = re.compile(r"tera|dynamax|z-?power|z-?move|\bzud\b", re.I)
# Ruby that defines a forbidden battle option: a method (pbTerastallize, pbCanDynamax?,
# pbUseZMove...) or a setting/switch constant (NO_TERASTALLIZE, DYNAMAX_..., NO_ZMOVE...).
GIMMICK_DEF = re.compile(
    r"^\s*def\s+(?:self\.)?\w*(?:terastal|dynamax|gigantamax|zmove|z_move|zpower|z_power|zcrystal)\w*[?!]?"
    r"|^\s*(?:NO_)?\w*(?:TERASTAL|DYNAMAX|GIGANTAMAX|ZMOVE|Z_MOVE|ZPOWER|Z_POWER)\w*\s*=",
    re.I | re.M)


def _meta_name(meta):
    m = re.search(r"^\s*Name\s*=\s*(.+?)\s*$", meta.read_text(encoding="utf-8-sig"), re.M)
    return m.group(1) if m else ""


def _plugin_scripts():
    return sorted(PLUGINS.rglob("*.rb"))


def test_no_tera_dynamax_zmove_enabled():
    names = [_meta_name(m) for m in sorted(PLUGINS.glob("*/meta.txt"))]
    assert "Generation 9 Pack" in names  # the check below must run against the installed pack
    assert [n for n in names if GIMMICK_PLUGIN_NAME.search(n)] == []
    found = []
    for rb in _plugin_scripts():
        for m in GIMMICK_DEF.finditer(rb.read_text(encoding="utf-8", errors="replace")):
            found.append(f"{rb.relative_to(PLUGINS).as_posix()}: {m.group(0).strip()}")
    assert found == []


def test_gimmick_pattern_catches_the_known_plugins():
    # The patterns must match what those plugins actually look like, or the test above proves nothing.
    for name in ["[DBK] Terastallization", "[DBK] Dynamax", "[DBK] Z-Power", "ZUD Plugin"]:
        assert GIMMICK_PLUGIN_NAME.search(name), name
    for line in ["  def pbTerastallize(idxBattler)", "  def pbCanDynamax?(idxBattler)",
                 "  def pbUseZMove(idxBattler)", "  NO_TERASTALLIZE = 66", "  NO_ZMOVE = 64"]:
        assert GIMMICK_DEF.search(line), line
    # The Gen 9 Pack's own Tera-named content (Terapagos, Tera Shell) and pbEffectAfterAllHits are fine.
    for line in ["  def pbEffectAfterAllHits(user, target)", "Battle::AbilityEffects.add(:TERASHELL,"]:
        assert not GIMMICK_DEF.search(line), line


def test_gimmicks_plugin_names_every_blocked_plugin():
    src = GIMMICKS.read_text(encoding="utf-8")
    listed = re.findall(r'"([^"]+)"', re.search(r"GIMMICK_PLUGINS\s*=\s*\[(.*?)\n\s*\]", src, re.S).group(1))
    for name in ["[DBK] Terastallization", "[DBK] Dynamax", "[DBK] Z-Power"]:
        assert name in listed
    assert all(GIMMICK_PLUGIN_NAME.search(n) for n in listed)


def test_mega_evolution_is_not_switched_off():
    # Essentials disables Mega Evolution through the game switch Settings::NO_MEGA_EVOLUTION.
    for rb in _plugin_scripts():
        src = rb.read_text(encoding="utf-8", errors="replace")
        assert not re.search(r"^\s*NO_MEGA_EVOLUTION\s*=", src, re.M), rb
        assert not re.search(r"NO_MEGA_EVOLUTION\]\s*=\s*true", src), rb


def test_classic_gen9_rules_override_champions_mechanics():
    # Director 2026-10-19: classic Gen 9 rules. PSC_Gimmicks loads after the pack and turns them off.
    src = GIMMICKS.read_text(encoding="utf-8")
    assert re.search(r"^\s*CHAMPIONS_MECHANICS\s*=\s*false\s*$", src, re.M)
    meta = (GIMMICKS.parent / "meta.txt").read_text(encoding="utf-8")
    assert re.search(r"^\s*Requires\s*=\s*Generation 9 Pack\b", meta, re.M)
