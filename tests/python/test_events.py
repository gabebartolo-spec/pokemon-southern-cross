"""Map events from tmj objects: each type reproduces a real base Essentials event (fixtures)."""
import json
from pathlib import Path

import pytest

from tools.maps import build, events
from tools.rmxp import marshal

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "game" / "Data"
FIXTURES = ROOT / "tests" / "fixtures" / "events"
FIXTURE_NAMES = sorted(p.stem for p in FIXTURES.glob("*.json"))


def fixture(name):
    return json.loads((FIXTURES / (name + ".json")).read_text(encoding="utf-8"))


def built(fx):
    return events.to_plain(events.build(fx["object"], eid=fx["event_id"]))


def commands(ev, page=0):
    return [(c.ivars["@indent"], c.ivars["@code"], events.to_plain(c.ivars["@parameters"]))
            for c in ev.ivars["@pages"][page].ivars["@list"]]


def o(name, typ, x=1, y=1, **props):
    plist = [{"name": k, "type": "string", "value": v} for k, v in props.items()]
    return {"id": 1, "name": name, "type": typ, "x": x * 32, "y": y * 32, "properties": plist}


def test_fixtures_cover_every_type():
    kinds = {fixture(n)["object"]["type"] for n in FIXTURE_NAMES}
    assert kinds == set(events.BUILDERS) - {"script"}  # script has no base pattern to copy


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_is_the_base_event(name):
    fx = fixture(name)
    base = marshal.loads((DATA / ("Map%03d.rxdata" % fx["map"])).read_bytes())
    assert events.to_plain(base.ivars["@events"][fx["event_id"]]) == fx["event"]


def test_trainer_event_matches_base_fixture():
    for name in ("trainer", "trainer_doubles"):
        fx = fixture(name)
        assert built(fx) == fx["event"], name
    ev = fixture("trainer")["event"]
    assert ev["@name"] == "Trainer(2)"
    assert [c[1] for c in ev["@pages"][0]["@list"]] == [355, 355, 101, 111, 123, 0, 412, 355, 0]


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_event_matches_base_fixture(name):
    fx = fixture(name)
    assert built(fx) == fx["event"]


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_built_event_uses_base_ivar_order(name):
    ev = events.build(fixture(name)["object"])
    assert list(ev.ivars) == events.EVENT_IVARS == build.EVENT_IVARS
    for page in ev.ivars["@pages"]:
        assert list(page.ivars) == events.PAGE_IVARS == build.PAGE_IVARS
    assert marshal.loads(marshal.dumps(ev)).cls == "RPG::Event"


def test_warp_event_transfers_player():
    ev = events.build({"id": 1, "name": "Gate", "type": "warp", "x": 64, "y": 32,
                       "properties": [{"name": "target_map", "value": 2}, {"name": "target_x", "value": 8},
                                      {"name": "target_y", "value": 7}, {"name": "direction", "value": "up"}]})
    assert (ev.ivars["@x"], ev.ivars["@y"], ev.ivars["@name"].text) == (2, 1, "Gate")
    page = ev.ivars["@pages"][0]
    assert page.ivars["@trigger"] == events.TRIGGERS["player_touch"]
    assert [c[1] for c in commands(ev)] == [223, 106, 201, 223, 0]
    assert commands(ev)[2] == (0, 201, [0, 2, 8, 7, 8, 1])


def test_unknown_type_rejected():
    with pytest.raises(events.MapBuildError) as e:
        events.build(o("Thing", "teleporter"))
    assert "Thing" in str(e.value) and "teleporter" in str(e.value)
    assert events.MapBuildError is build.MapBuildError


def test_trainer_lose_text_uses_the_engine_speech_argument():
    ev = events.build(o("Kid", "trainer", trainer="YOUNGSTER,Ben", sight=3, intro="Oi!",
                        lose="You're good, mate. Don't tell \\PN I said so."))
    assert ev.ivars["@name"].text == "Trainer(3)"
    branch = [c for c in commands(ev) if c[1] == 111][0]
    assert branch[2] == [12, "TrainerBattle.start([:YOUNGSTER, \"Ben\", 0, "
                             "'You\\'re good, mate. Don\\'t tell \\\\PN I said so.'])"]
    # With no after-battle line, the trainer repeats the lose line when talked to again.
    assert commands(ev, 1)[0] == (0, 101, ["You're good, mate. Don't tell \\PN I said so."])


def test_trainer_with_nothing_to_say_after_has_an_empty_second_page():
    ev = events.build(o("Kid", "trainer", trainer="YOUNGSTER, Ben", sight=1, intro="Oi!"))
    assert commands(ev, 1) == [(0, 0, [])]
    assert ev.ivars["@pages"][1].ivars["@condition"].ivars["@self_switch_valid"] is True
    assert [c for c in commands(ev) if c[1] == 111][0][2][1] == 'TrainerBattle.start(:YOUNGSTER, "Ben")'


@pytest.mark.parametrize("spec", ["YOUNGSTER", "youngster,Ben", "YOUNGSTER,", 'YOUNGSTER,Be"n', "YOUNGSTER,#{x}"])
def test_bad_trainer_spec_rejected(spec):
    with pytest.raises(events.MapBuildError):
        events.build(o("Kid", "trainer", trainer=spec, sight=2, intro="Oi!"))


def test_trainer_needs_sight_and_intro():
    with pytest.raises(events.MapBuildError):
        events.build(o("Kid", "trainer", trainer="YOUNGSTER,Ben", intro="Oi!"))
    with pytest.raises(events.MapBuildError):
        events.build(o("Kid", "trainer", trainer="YOUNGSTER,Ben", sight=2))


def test_item_quantity_uses_the_base_form():
    ev = events.build(o("Lollies", "item", item="RARECANDY", quantity=2))
    assert commands(ev)[0] == (0, 111, [12, "pbItemBall(:RARECANDY, 2)"])  # as Map021 event 27
    with pytest.raises(events.MapBuildError):
        events.build(o("Lollies", "item", item="Rare Candy"))


def test_text_boxes_and_lines():
    ev = events.build(o("Bloke", "npc", graphic="NPC 01", direction="left",
                        text="G'day.\n\nNice arvo for it,\nisn't it?"))
    assert commands(ev) == [(0, 101, ["G'day."]), (0, 101, ["Nice arvo for it,"]),
                            (0, 401, ["isn't it?"]), (0, 0, [])]
    assert ev.ivars["@pages"][0].ivars["@graphic"].ivars["@direction"] == 4


def test_npc_needs_graphic_and_text():
    with pytest.raises(events.MapBuildError):
        events.build(o("Bloke", "npc", text="G'day."))
    with pytest.raises(events.MapBuildError):
        events.build(o("Bloke", "npc", graphic="NPC 01"))


def test_script_event_is_one_script_command():
    ev = events.build(o("Gate check", "script", trigger="autorun", script="pbSetSelfSwitch(1,\n  \"A\", true)"))
    assert commands(ev) == [(0, 355, ["pbSetSelfSwitch(1,"]), (0, 655, ['  "A", true)']), (0, 0, [])]
    assert ev.ivars["@pages"][0].ivars["@trigger"] == events.TRIGGERS["autorun"]
    with pytest.raises(events.MapBuildError):
        events.build(o("Gate check", "script", trigger="sometimes", script="p 1"))
