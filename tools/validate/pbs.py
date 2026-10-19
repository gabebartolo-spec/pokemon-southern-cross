"""Readers for Pokémon Essentials v21.1 PBS text files.

Formats, taken from game/PBS (read the real files before changing this):

* trainers.txt: `[TYPE,Name]` or `[TYPE,Name,version]` section headers, then `Key = Value`
  lines. `Pokemon = SPECIES,level` repeats once per team member; indented lines under it
  (Moves, Item, ...) belong to that member. `#---` lines are separators.
* encounters.txt: `[mapid]` or `[mapid,version]` headers (a `# comment` may follow), then
  encounter-type lines `Land,21` / `OldRod` (name, optional step chance), each followed by
  indented slot lines `chance,SPECIES,minlevel[,maxlevel]`.

Files start with a UTF-8 BOM; lines starting with `#` are comments.
"""
from pathlib import Path


def _lines(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    for raw in text.splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            yield line


def _header(line):
    """`[A,B] # note` -> 'A,B' or None when the line is not a section header."""
    if not line.startswith("["):
        return None
    end = line.find("]")
    return line[1:end].strip() if end > 0 else None


def read_sections(path):
    """Return [(header, [(key, value), ...])] in file order; repeated keys are kept."""
    sections = []
    for line in _lines(path):
        h = _header(line)
        if h is not None:
            sections.append((h, []))
        elif sections and "=" in line:
            key, value = line.split("=", 1)
            sections[-1][1].append((key.strip(), value.strip()))
    return sections


def read_section_file(path):
    """`[SECTION]` headers and `Key = Value` lines -> {header: {key: value}} (last repeat wins)."""
    return {h: dict(pairs) for h, pairs in read_sections(path)}


def trainer_id(header):
    """Normalise a trainers.txt header: version 0 is the same trainer as no version."""
    parts = [p.strip() for p in header.split(",")]
    if len(parts) >= 3 and parts[2] in ("", "0"):
        parts = parts[:2]
    return ",".join(parts)


def read_trainers(path):
    """{normalised trainer id: [(species, level), ...]} from trainers.txt."""
    out = {}
    for header, pairs in read_sections(path):
        team = []
        for key, value in pairs:
            if key == "Pokemon":
                species, level = [p.strip() for p in value.split(",")[:2]]
                team.append((species, int(level)))
        out[trainer_id(header)] = team
    return out


def read_encounters(path):
    """{map id (str): [(encounter type, species, min level, max level), ...]} from encounters.txt.

    A map's versions (`[005,1]`) are merged under the map id.
    """
    out, current, etype = {}, None, None
    for line in _lines(path):
        h = _header(line)
        if h is not None:
            current = h.split(",")[0].strip().lstrip("0") or "0"
            out.setdefault(current, [])
            etype = None
        elif current is None:
            continue
        elif line[0].isdigit() and line.split(",")[0].strip().isdigit() and etype is not None \
                and len(line.split(",")) >= 3:
            chance, species, lo, *hi = [p.strip() for p in line.split(",")]
            out[current].append((etype, species, int(lo), int(hi[0]) if hi else int(lo)))
        else:
            etype = line.split(",")[0].strip()
    return out
