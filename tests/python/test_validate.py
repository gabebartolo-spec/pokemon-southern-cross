"""Tests for the content validators (tools/validate/). Fixtures are small synthetic repos."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.validate import content, pbs  # noqa: E402

REGISTER = """# Licensing register

| Item | Source URL | Version | Terms (one line) | Credit line | Status | Paths |
|---|---|---|---|---|---|---|
| Pokémon Essentials | u | v | t | c | CLEARED | `game/**` (base-manifest) |
| Gen 3 sprites | u | v | t | c | CLEARED | `game/Graphics/Pokemon/Front/TEST*.png`, `game/Graphics/Pokemon/Back/TEST*.png` |
"""
TRAINERS = "\ufeff# header\n#---\n[LEADER,Rex]\nLoseText = x\nPokemon = TESTA,{lvl}\n    Moves = TACKLE\n"
ENCOUNTERS = "\ufeff# header\n#---\n[007] # Route\nLand,21\n    60,{sp},{lo},{hi}\n    40,TESTA,3\n"


def png(repo, kind, species, data=b"gen3"):
    p = repo / "game" / "Graphics" / "Pokemon" / kind / f"{species}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def make_repo(tmp_path, cap=15, lvl=10, species=("TESTA",), enc_species="TESTA", enc_hi=8,
              trainers=("LEADER,Rex",), maps=(7,)):
    r = tmp_path
    (r / "content").mkdir()
    (r / "docs").mkdir()
    (r / "game" / "PBS").mkdir(parents=True)
    (r / "docs" / "LICENSING_REGISTER.md").write_text(REGISTER, encoding="utf-8")
    (r / "content" / "progression.json").write_text(json.dumps(
        {"segments": [{"id": "gym1", "cap": cap, "trainers": list(trainers), "maps": list(maps)}]}))
    (r / "content" / "dex.json").write_text(json.dumps({"regional": list(species)}))
    (r / "game" / "PBS" / "trainers.txt").write_text(TRAINERS.format(lvl=lvl), encoding="utf-8")
    (r / "game" / "PBS" / "encounters.txt").write_text(
        ENCOUNTERS.format(sp=enc_species, lo=5, hi=enc_hi), encoding="utf-8")
    base = r / "game" / "Data" / "base.txt"
    base.parent.mkdir()
    base.write_bytes(b"base file")
    manifest = [f"{hashlib.sha256(b'base file').hexdigest()}  Data/base.txt",
                f"{'0' * 64}  PBS/trainers.txt", f"{'0' * 64}  PBS/encounters.txt"]
    (r / "game" / ".psc_base_manifest.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    for sp in species:
        png(r, "Front", sp)
        png(r, "Back", sp)
    return r


def test_valid_fixture_passes(tmp_path):
    assert content.validate(make_repo(tmp_path)) == []


def test_trainer_over_cap_rejected(tmp_path):
    errors = content.validate(make_repo(tmp_path, cap=15, lvl=16))
    assert len(errors) == 1 and "LEADER,Rex" in errors[0]


def test_trainer_missing_from_trainers_txt_rejected(tmp_path):
    errors = content.validate(make_repo(tmp_path, trainers=("LEADER,Nobody",)))
    assert len(errors) == 1 and "LEADER,Nobody" in errors[0]


def test_encounter_over_cap_rejected(tmp_path):
    errors = content.validate(make_repo(tmp_path, cap=15, enc_hi=16))
    assert len(errors) == 1 and "map 7" in errors[0]


def test_encounter_species_must_be_in_dex(tmp_path):
    errors = content.validate(make_repo(tmp_path, enc_species="OTHER"))
    assert len(errors) == 1 and "OTHER" in errors[0]


def test_every_encounter_species_has_gen3_sprites(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "game" / "Graphics" / "Pokemon" / "Back" / "TESTA.png").unlink()
    errors = content.validate(repo)
    assert len(errors) == 1 and "Back/TESTA.png" in errors[0]


def test_sprite_matching_base_hash_rejected(tmp_path):
    repo = make_repo(tmp_path)
    data = b"base essentials sprite"
    png(repo, "Front", "TESTA", data)
    manifest = repo / "game" / ".psc_base_manifest.txt"
    manifest.write_text(manifest.read_text(encoding="utf-8")
                        + f"{hashlib.sha256(data).hexdigest()}  Graphics/Pokemon/Front/TESTA.png\n",
                        encoding="utf-8")
    errors = content.validate(repo)
    assert any("Front/TESTA.png" in e and "base" in e for e in errors)


def test_added_file_needs_register_entry(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "game" / "Graphics" / "stray.png").write_bytes(b"x")
    errors = content.validate(repo)
    assert len(errors) == 1 and "Graphics/stray.png" in errors[0]


def test_essentials_glob_does_not_clear_added_files(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "game" / "Data" / "new.txt").write_bytes(b"new")
    assert any("Data/new.txt" in e for e in content.validate(repo))


def test_pbs_read_section_file(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("\ufeff# c\n[A,b]\nKey = Val\nOther=1\n#---\n[C]\nK = v\n", encoding="utf-8")
    assert pbs.read_section_file(p) == {"A,b": {"Key": "Val", "Other": "1"}, "C": {"K": "v"}}


def test_pbs_trainer_version_zero_equals_no_version(tmp_path):
    p = tmp_path / "t.txt"
    p.write_text("[A,B,0]\nPokemon = X,5\n[A,B,2]\nPokemon = Y,6\n", encoding="utf-8")
    assert pbs.read_trainers(p) == {"A,B": [("X", 5)], "A,B,2": [("Y", 6)]}


def test_real_repo_is_valid():
    assert content.validate(ROOT) == []


def test_overwritten_base_sprite_needs_register_entry(tmp_path):
    repo = make_repo(tmp_path)
    gfx = repo / "game" / "Graphics" / "base.png"
    gfx.write_bytes(b"orig")
    manifest = repo / "game" / ".psc_base_manifest.txt"
    manifest.write_text(manifest.read_text(encoding="utf-8")
                        + f"{hashlib.sha256(b'orig').hexdigest()}  Graphics/base.png\n", encoding="utf-8")
    assert content.validate(repo) == []
    gfx.write_bytes(b"overwritten")
    errors = content.validate(repo)
    assert len(errors) == 1 and "Graphics/base.png" in errors[0] and "overwrites" in errors[0]
    reg = repo / "docs" / "LICENSING_REGISTER.md"
    reg.write_text(reg.read_text(encoding="utf-8")
                   + "| Replacement | u | v | t | c | CLEARED | `game/Graphics/base.png` |\n", encoding="utf-8")
    assert content.validate(repo) == []


def test_trainer_without_pokemon_rejected(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "game" / "PBS" / "trainers.txt").write_text("[LEADER,Rex]\nLoseText = x\n", encoding="utf-8")
    errors = content.validate(repo)
    assert len(errors) == 1 and "no Pokemon lines" in errors[0]


def test_segment_map_without_encounters_rejected(tmp_path):
    errors = content.validate(make_repo(tmp_path, maps=(7, 9)))
    assert len(errors) == 1 and "map 9" in errors[0] and "no encounters" in errors[0]


def test_unparseable_encounter_line_rejected(tmp_path):
    repo = make_repo(tmp_path)
    enc = repo / "game" / "PBS" / "encounters.txt"
    enc.write_text(enc.read_text(encoding="utf-8") + "    50,TESTA\n", encoding="utf-8")
    errors = content.validate(repo)
    assert len(errors) == 1 and "cannot parse" in errors[0]


def test_lfs_pointer_hashes_as_its_content(tmp_path):
    repo = make_repo(tmp_path)
    audio = repo / "game" / "Audio" / "a.mid"
    audio.parent.mkdir()
    digest = hashlib.sha256(b"midi bytes").hexdigest()
    audio.write_bytes(f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize 10\n".encode())
    manifest = repo / "game" / ".psc_base_manifest.txt"
    manifest.write_text(manifest.read_text(encoding="utf-8") + f"{digest}  Audio/a.mid\n", encoding="utf-8")
    assert content.validate(repo) == []
