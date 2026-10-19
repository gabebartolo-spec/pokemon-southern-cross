#!/usr/bin/env python3
"""Validate our own content (not base Essentials) against the design's hard limits.

Scope: trainers listed in content/progression.json segments (looked up in game/PBS/trainers.txt),
encounters for the maps those segments list (game/PBS/encounters.txt), sprites for the species in
content/dex.json "regional", and every file under game/ that is not an unmodified base file.

`validate(repo_root)` returns error strings; an empty list is valid. Run as a script it prints
the errors and `CHECKS <n>`, where n is the number of validation rules run (len(RULES)).

`--emit-caps` writes the level caps (badges held before a segment -> that segment's cap) from
content/progression.json to every path in CAPS_FILES: content/caps.json for people and tools,
game/Data/psc_caps.json for the PSC_Difficulty plugin, which reads it at runtime.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from . import pbs
except ImportError:  # run as a script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pbs

MANIFEST = "game/.psc_base_manifest.txt"
CAPS_FILES = ("content/caps.json", "game/Data/psc_caps.json")
BASE_MARKER = "base-manifest"


def _json(root, rel):
    return json.loads((Path(root) / rel).read_text(encoding="utf-8"))


def _segments(root):
    return _json(root, "content/progression.json")["segments"]


def _dex(root):
    return set(_json(root, "content/dex.json")["regional"])


def _manifest(root):
    """{path relative to game/: sha256}"""
    out = {}
    for line in (Path(root) / MANIFEST).read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, path = line.split("  ", 1)
            out[path] = digest
    return out


def _sha(path):
    """sha256 of the file's content. CI checks out without LFS, so an LFS pointer file stands
    for its content: its `oid sha256:` is the content hash."""
    data = Path(path).read_bytes()
    if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
        m = re.search(rb"^oid sha256:([0-9a-f]{64})$", data, re.M)
        if m:
            return m.group(1).decode()
    return hashlib.sha256(data).hexdigest()


def _glob_re(glob):
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**", i):
            out += ".*"
            i += 2
        elif glob[i] == "*":
            out += "[^/]*"
            i += 1
        elif glob[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(glob[i])
            i += 1
    return re.compile(out + r"\Z")


def _register_globs(root):
    """Path globs from the register's Paths column (read by header name). The Essentials row
    (Item starts with 'Pokémon Essentials', or Paths holds `base-manifest`) covers manifest
    files only, so it is not returned here."""
    globs, header = [], None
    text = (Path(root) / "docs" / "LICENSING_REGISTER.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        row = dict(zip(header, cells))
        item, paths = row.get("Item", ""), row.get("Paths", "")
        if item.startswith("Pokémon Essentials") or BASE_MARKER in paths:
            continue
        globs += re.findall(r"`([^`]+)`", paths)
    return globs


def added_files(root):
    """Files under game/ whose path is not in the base manifest. Edits to base files (PBS, the
    compiled Data) are not additions; they are reviewed in their PR."""
    manifest = _manifest(root)
    game = Path(root) / "game"
    out = []
    for p in sorted(game.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(game).as_posix()
        if f"game/{rel}" == MANIFEST:
            continue
        if rel not in manifest:
            out.append(rel)
    return out


def overwritten_assets(root):
    """Base paths under Graphics/ or Audio/ whose bytes differ from the manifest hash."""
    manifest = _manifest(root)
    out = []
    for rel, digest in sorted(manifest.items()):
        if rel.startswith(("Graphics/", "Audio/")):
            p = Path(root) / "game" / rel
            if p.is_file() and _sha(p) != digest:
                out.append(rel)
    return out


# ---- rules: each takes repo_root and returns a list of error strings ----

def rule_trainers_listed_exist(root):
    known = pbs.read_trainers(Path(root) / "game/PBS/trainers.txt")
    return [f"{seg['id']}: trainer {t} is not in trainers.txt"
            for seg in _segments(root) for t in seg["trainers"] if pbs.trainer_id(t) not in known] +            [f"{seg['id']}: trainer {t} has no Pokemon lines"
            for seg in _segments(root) for t in seg["trainers"]
            if pbs.trainer_id(t) in known and not known[pbs.trainer_id(t)]]


def rule_trainers_within_cap(root):
    known = pbs.read_trainers(Path(root) / "game/PBS/trainers.txt")
    errors = []
    for seg in _segments(root):
        for t in seg["trainers"]:
            for species, level in known.get(pbs.trainer_id(t), []):
                if level > seg["cap"]:
                    errors.append(f"{seg['id']}: trainer {t} has {species} at level {level}, "
                                  f"over cap {seg['cap']}")
    return errors


def _segment_encounters(root):
    enc = pbs.read_encounters(Path(root) / "game/PBS/encounters.txt")
    for seg in _segments(root):
        for m in seg["maps"]:
            yield seg, str(int(m)), enc.get(str(int(m)), [])


def rule_encounters_present_and_parsable(root):
    enc = pbs.read_encounters(Path(root) / "game/PBS/encounters.txt")
    errors = [f"{seg['id']}: map {m} has no encounters in encounters.txt"
              for seg in _segments(root) for m in map(lambda x: str(int(x)), seg["maps"])
              if not enc.get(m)]
    return errors + [f"encounters.txt map {m}: cannot parse line {bad!r}"
                     for m, bad in pbs.bad_encounter_lines(Path(root) / "game/PBS/encounters.txt")
                     if m in {str(int(x)) for seg in _segments(root) for x in seg["maps"]}]


def rule_encounters_within_cap(root):
    return [f"{seg['id']}: map {m} {et} {sp} up to level {hi}, over cap {seg['cap']}"
            for seg, m, slots in _segment_encounters(root)
            for et, sp, lo, hi in slots if hi > seg["cap"]]


def rule_encounter_species_in_dex(root):
    dex = _dex(root)
    return [f"{seg['id']}: map {m} {et} species {sp} is not in content/dex.json"
            for seg, m, slots in _segment_encounters(root)
            for et, sp, lo, hi in slots if sp not in dex]


def rule_dex_sprites_exist(root):
    errors = []
    for sp in sorted(_dex(root)):
        for kind in ("Front", "Back"):
            if not (Path(root) / f"game/Graphics/Pokemon/{kind}/{sp}.png").is_file():
                errors.append(f"missing sprite game/Graphics/Pokemon/{kind}/{sp}.png")
    return errors


def rule_dex_sprites_not_base(root):
    base_hashes = set(_manifest(root).values())
    errors = []
    for sp in sorted(_dex(root)):
        for kind in ("Front", "Back"):
            p = Path(root) / f"game/Graphics/Pokemon/{kind}/{sp}.png"
            if p.is_file() and _sha(p) in base_hashes:
                errors.append(f"sprite {kind}/{sp}.png is a base Essentials sprite, "
                              f"not from the Gen 3 pack")
    return errors


def caps_text(root):
    """The caps file text: {"<badges held before the segment>": cap}, one flat line. Segment i is
    reached with i badges. The plugin's parser (PSC::Rules.parse_caps) accepts only this shape."""
    caps = {str(i): int(seg["cap"]) for i, seg in enumerate(_segments(root))}
    return json.dumps(caps) + "\n"


def emit_caps(root):
    text = caps_text(root)
    for rel in CAPS_FILES:
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    return text


def rule_caps_in_sync(root):
    want = caps_text(root)
    errors = []
    for rel in CAPS_FILES:
        path = Path(root) / rel
        if not path.is_file():
            errors.append(f"{rel} is missing; run tools/validate/content.py --emit-caps")
        elif path.read_text(encoding="utf-8") != want:
            errors.append(f"{rel} is out of sync with content/progression.json; "
                          f"run tools/validate/content.py --emit-caps")
    return errors


def rule_added_files_registered(root):
    patterns = [_glob_re(g) for g in _register_globs(root)]
    return [f"game/{rel} is not in the base manifest and matches no Paths glob in "
            f"docs/LICENSING_REGISTER.md"
            for rel in added_files(root) if not any(p.match(f"game/{rel}") for p in patterns)] +            [f"game/{rel} overwrites a base asset and matches no Paths glob in "
            f"docs/LICENSING_REGISTER.md"
            for rel in overwritten_assets(root) if not any(p.match(f"game/{rel}") for p in patterns)]


RULES = [rule_trainers_listed_exist, rule_trainers_within_cap,
         rule_encounters_present_and_parsable, rule_encounters_within_cap,
         rule_encounter_species_in_dex, rule_dex_sprites_exist, rule_dex_sprites_not_base,
         rule_added_files_registered, rule_caps_in_sync]


def validate(repo_root):
    errors = []
    for rule in RULES:
        errors += rule(repo_root)
    return errors


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = Path(__file__).resolve().parents[2]
    if "--emit-caps" in argv:
        print(f"caps {emit_caps(root).strip()} -> {', '.join(CAPS_FILES)}")
    errors = validate(root)
    for e in errors:
        print(f"ERROR {e}")
    print(f"CHECKS {len(RULES)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
