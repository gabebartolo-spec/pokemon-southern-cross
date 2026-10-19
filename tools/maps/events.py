"""Map events built from Tiled objects, in Essentials v21.1's own event patterns.

    build(obj, eid=1, ctx=None) -> RubyObject("RPG::Event")

``obj`` is one object of a tmj ``events`` layer (``type``, ``name``, ``x``, ``y``, ``properties``).
Each type copies the command list of a real base event (fixtures in tests/fixtures/events/):

- warp     Map003 event 1   fade out, wait, transfer, fade in (player touch)
- sign     Map049 event 9   text, no graphic (action button)
- npc      Map002 event 3   text, a character graphic (action button)
- item     Map005 event 11  pbItemBall, then self switch A hides the ball
- trainer  Map031 event 4   (doubles: event 10) named Trainer(sight), TrainerBattle.start,
                            self switch A, then an after-battle page
- script   one Script command (355, continued by 655 lines)

Text is the author's: it is written as given (blank line = new box, newline = next line of the
same box). ``ctx`` (from build.py) checks cross references: warp targets, items, trainers and
character graphics; with ``ctx=None`` only the object itself is checked.

    python tools/maps/events.py <map_id> <event_id>   # a base event as plain JSON (fixtures)
"""
import json
import re
import struct
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.rmxp.marshal import RString, RubyObject, UserDef, loads  # noqa: E402

TILE = 32
DIRECTIONS = {"retain": 0, "down": 2, "left": 4, "right": 6, "up": 8}
TRIGGERS = {"action": 0, "player_touch": 1, "event_touch": 2, "autorun": 3, "parallel": 4}
TONE_BLACK, TONE_CLEAR = (-255.0, -255.0, -255.0, 0.0), (0.0, 0.0, 0.0, 0.0)
FADE_FRAMES, WARP_WAIT_FRAMES = 6, 8
ITEM_BALL_GRAPHIC = "Object ball"
TRAINER_GRAPHIC = "trainer_%s"
SE_VOLUME, SE_PITCH = 80, 100
# Event command codes (RPG Maker XP).
END, TEXT, TEXT_MORE, BRANCH, BRANCH_END = 0, 101, 401, 111, 412
SELF_SWITCH, WAIT, TRANSFER, TINT, PLAY_SE, SCRIPT, SCRIPT_MORE = 123, 106, 201, 223, 250, 355, 655
BRANCH_SCRIPT, SWITCH_ON = 12, 0

EVENT_IVARS = ["@pages", "@name", "@y", "@x", "@id"]
PAGE_IVARS = ["@move_type", "@list", "@condition", "@direction_fix", "@move_route", "@trigger",
              "@step_anime", "@move_frequency", "@graphic", "@always_on_top", "@walk_anime",
              "@move_speed", "@through"]

ID_SYMBOL = re.compile(r"^[A-Z0-9_]+$")
UNSAFE_IN_RUBY_STRING = re.compile(r'["\\]|#\{')


class MapBuildError(Exception):
    pass


def s(text):
    return RString.utf8(text)


def obj(cls, ivars):
    return RubyObject(cls, dict(ivars))


def audio(name, volume, pitch):
    return obj("RPG::AudioFile", [("@volume", int(volume)), ("@name", s(name)), ("@pitch", int(pitch))])


def cmd(code, params, indent=0):
    return obj("RPG::EventCommand", [("@parameters", params), ("@indent", indent), ("@code", code)])


def tone(rgbg):
    return UserDef("Tone", struct.pack("<4d", *rgbg))


def page(commands, trigger, graphic="", direction=2, self_switch=None):
    """One event page with the base defaults; ``self_switch`` 'A' makes it the A-is-on page."""
    condition = obj("RPG::Event::Page::Condition", [
        ("@switch2_valid", False), ("@self_switch_ch", s(self_switch or "A")), ("@switch1_id", 1),
        ("@switch1_valid", False), ("@variable_value", 0), ("@self_switch_valid", self_switch is not None),
        ("@variable_id", 1), ("@variable_valid", False), ("@switch2_id", 1)])
    route = obj("RPG::MoveRoute", [("@list", [obj("RPG::MoveCommand", [("@parameters", []), ("@code", 0)])]),
                                   ("@skippable", False), ("@repeat", True)])
    gfx = obj("RPG::Event::Page::Graphic", [
        ("@opacity", 255), ("@character_name", s(graphic)), ("@pattern", 0), ("@tile_id", 0),
        ("@direction", direction), ("@blend_type", 0), ("@character_hue", 0)])
    v = {"@move_type": 0, "@list": commands + [cmd(END, [])], "@condition": condition,
         "@direction_fix": False, "@move_route": route, "@trigger": trigger, "@step_anime": False,
         "@move_frequency": 3, "@graphic": gfx, "@always_on_top": False, "@walk_anime": True,
         "@move_speed": 3, "@through": False}
    return obj("RPG::Event::Page", [(k, v[k]) for k in PAGE_IVARS])


def cell(o):
    """The tile an object stands on: floor(x/32), floor(y/32)."""
    try:
        return int(float(o.get("x", 0))) // TILE, int(float(o.get("y", 0))) // TILE
    except (TypeError, ValueError):
        raise MapBuildError("object %r: x and y must be numbers" % o.get("name"))


def props_of(o, where):
    out = {}
    for p in o.get("properties") or []:
        try:
            out[p["name"]] = p["value"]
        except (KeyError, TypeError):
            raise MapBuildError("%s: malformed property %r" % (where, p))
    return out


# ---------------------------------------------------------------- property readers

def _int(props, key, where, default=None, minimum=None):
    v = props.get(key, default)
    if not isinstance(v, int) or isinstance(v, bool) or (minimum is not None and v < minimum):
        raise MapBuildError("%s: needs integer property %s%s"
                            % (where, key, "" if minimum is None else " (%d or more)" % minimum))
    return v


def _text(props, key, where, required=True):
    v = props.get(key)
    if v is None and not required:
        return None
    if not isinstance(v, str) or not v.strip():
        raise MapBuildError("%s: needs text property %s" % (where, key))
    return v


def _choice(props, key, table, default, where, allowed=None):
    v = props.get(key, default)
    if v not in table or (allowed is not None and v not in allowed):
        raise MapBuildError("%s: %s must be one of %s" % (where, key, ", ".join(allowed or table)))
    return table[v]


def _symbol(value, what, where):
    if not isinstance(value, str) or not ID_SYMBOL.match(value):
        raise MapBuildError("%s: %s must be an Essentials id like POTION (A-Z, 0-9, _), got %r"
                            % (where, what, value))
    return value


def messages(text, indent=0):
    """Show Text commands: a blank line starts a new box, a newline continues the same box."""
    out = []
    for box in re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n")):
        lines = box.split("\n")
        out.append(cmd(TEXT, [s(lines[0])], indent))
        out += [cmd(TEXT_MORE, [s(line)], indent) for line in lines[1:]]
    return out


def _script(lines, indent=0):
    return [cmd(SCRIPT if i == 0 else SCRIPT_MORE, [s(line)], indent) for i, line in enumerate(lines)]


def _branch_then_switch(script, before=()):
    """Conditional branch on a script; when true: (before), self switch A on. Base trainer/item."""
    return ([cmd(BRANCH, [BRANCH_SCRIPT, s(script)])] + list(before)
            + [cmd(SELF_SWITCH, [s("A"), SWITCH_ON], 1), cmd(END, [], 1), cmd(BRANCH_END, [])])


def _graphic(props, where, ctx, required):
    g = props.get("graphic", "")
    if not isinstance(g, str) or (required and not g):
        raise MapBuildError("%s: needs property graphic (a file in Graphics/Characters)" % where)
    if g and ctx is not None and not ctx.has_character(g):
        raise MapBuildError("%s: graphic %r is not in game/Graphics/Characters" % (where, g))
    return g


# ---------------------------------------------------------------- types

def warp_commands(props, where, ctx):
    target = _int(props, "target_map", where)
    tx, ty = _int(props, "target_x", where), _int(props, "target_y", where)
    direction = _choice(props, "direction", DIRECTIONS, "retain", where)
    if ctx is not None:
        size = ctx.size(target)
        if size is None:
            raise MapBuildError("%s: warp target map %d does not exist" % (where, target))
        if not (0 <= tx < size[0] and 0 <= ty < size[1]):
            raise MapBuildError("%s: warp target (%d,%d) is outside map %d (%dx%d)"
                                % (where, tx, ty, target, size[0], size[1]))
        if not ctx.walkable(target, tx, ty):
            raise MapBuildError("%s: warp target (%d,%d) on map %d is not walkable" % (where, tx, ty, target))
    cmds = []
    if props.get("sound"):
        cmds.append(cmd(PLAY_SE, [audio(_text(props, "sound", where), SE_VOLUME, SE_PITCH)]))
    cmds += [cmd(TINT, [tone(TONE_BLACK), FADE_FRAMES]), cmd(WAIT, [WARP_WAIT_FRAMES]),
             cmd(TRANSFER, [0, target, tx, ty, direction, 1]),
             cmd(TINT, [tone(TONE_CLEAR), FADE_FRAMES])]
    return cmds


def _warp(o, props, where, ctx):
    return o.get("name") or "", [page(warp_commands(props, where, ctx), TRIGGERS["player_touch"])]


def _sign(o, props, where, ctx):
    return o.get("name") or "", [page(messages(_text(props, "text", where)), TRIGGERS["action"])]


def _npc(o, props, where, ctx):
    graphic = _graphic(props, where, ctx, required=True)
    direction = _choice(props, "direction", DIRECTIONS, "down", where, allowed=("down", "left", "right", "up"))
    return o.get("name") or "", [page(messages(_text(props, "text", where)), TRIGGERS["action"],
                                      graphic, direction)]


def _item(o, props, where, ctx):
    item = _symbol(props.get("item"), "item", where)
    quantity = _int(props, "quantity", where, default=1, minimum=1)
    if ctx is not None and not ctx.has_item(item):
        raise MapBuildError("%s: item %s is not in PBS/items.txt" % (where, item))
    call = "pbItemBall(:%s)" % item if quantity == 1 else "pbItemBall(:%s, %d)" % (item, quantity)
    return o.get("name") or "", [page(_branch_then_switch(call), TRIGGERS["action"], ITEM_BALL_GRAPHIC),
                                 page([], TRIGGERS["action"], "", self_switch="A")]


def _ruby_single_quoted(text):
    return "'%s'" % text.replace("\\", "\\\\").replace("'", "\\'")


def _trainer(o, props, where, ctx):
    spec = props.get("trainer")
    if not isinstance(spec, str) or spec.count(",") < 1:
        raise MapBuildError('%s: trainer must be "TYPE,Name" (e.g. "YOUNGSTER,Ben")' % where)
    ttype, name = (part.strip() for part in spec.split(",", 1))
    _symbol(ttype, "trainer type", where)
    if not name or UNSAFE_IN_RUBY_STRING.search(name):
        raise MapBuildError('%s: trainer name %r must be non-empty, without " \\ or #{' % (where, name))
    if ctx is not None and not ctx.has_trainer(ttype, name):
        raise MapBuildError("%s: trainer [%s,%s] is not in PBS/trainers.txt" % (where, ttype, name))
    sight = _int(props, "sight", where, minimum=1)
    direction = _choice(props, "direction", DIRECTIONS, "down", where, allowed=("down", "left", "right", "up"))
    doubles = props.get("doubles", False)
    if not isinstance(doubles, bool):
        raise MapBuildError("%s: doubles must be true or false" % where)
    intro = _text(props, "intro", where)
    lose = _text(props, "lose", where, required=False)
    after = _text(props, "after", where, required=False) or lose
    graphic = TRAINER_GRAPHIC % ttype
    if ctx is not None and not ctx.has_character(graphic):
        raise MapBuildError("%s: graphic %r is not in game/Graphics/Characters" % (where, graphic))
    if lose is None:
        battle = 'TrainerBattle.start(:%s, "%s")' % (ttype, name)
    else:  # Essentials' [type, name, version, lose text] form
        battle = 'TrainerBattle.start([:%s, "%s", 0, %s])' % (ttype, name, _ruby_single_quoted(lose))
    first = (_script(["pbTrainerIntro(:%s)" % ttype]) + _script(["pbNoticePlayer(get_self)"])
             + messages(intro) + (_script(['setBattleRule("double")']) if doubles else [])
             + _branch_then_switch(battle) + _script(["pbTrainerEnd"]))
    return "Trainer(%d)" % sight, [page(first, TRIGGERS["event_touch"], graphic, direction),
                                   page(messages(after) if after else [], TRIGGERS["action"], graphic,
                                        direction, self_switch="A")]


def _script_event(o, props, where, ctx):
    code = _text(props, "script", where)
    trigger = _choice(props, "trigger", TRIGGERS, "action", where)
    graphic = _graphic(props, where, ctx, required=False)
    direction = _choice(props, "direction", DIRECTIONS, "down", where, allowed=("down", "left", "right", "up"))
    return o.get("name") or "", [page(_script(code.replace("\r\n", "\n").split("\n")), trigger, graphic,
                                      direction)]


BUILDERS = {"warp": _warp, "sign": _sign, "npc": _npc, "item": _item, "trainer": _trainer,
            "script": _script_event}


def build(o, eid=1, ctx=None, where=None):
    """RubyObject('RPG::Event') for one tmj object; raises MapBuildError naming the object."""
    kind = o.get("type") or o.get("class") or ""
    where = where or "object %r (id %s)" % (o.get("name") or "", o.get("id"))
    if kind not in BUILDERS:
        raise MapBuildError("%s: unknown object type %r (%s, or spawn)" % (where, kind, ", ".join(BUILDERS)))
    x, y = cell(o)
    name, pages = BUILDERS[kind](o, props_of(o, where), where, ctx)
    return obj("RPG::Event", [("@pages", pages), ("@name", s(name)), ("@y", y), ("@x", x), ("@id", eid)])


# ---------------------------------------------------------------- plain JSON (fixtures)

def to_plain(v):
    """A marshal value as plain JSON data: objects as {"class", ivars...}, commands as
    [indent, code, parameters], Strings as text, Tone as {"Tone": [r, g, b, gray]}."""
    if isinstance(v, RString):
        return v.raw.decode("utf-8")
    if isinstance(v, RubyObject):
        if v.cls == "RPG::EventCommand":
            return [v.ivars["@indent"], v.ivars["@code"], to_plain(v.ivars["@parameters"])]
        out = {"class": v.cls}
        out.update((k, to_plain(x)) for k, x in v.ivars.items())
        return out
    if isinstance(v, UserDef):
        if v.cls == "Tone":
            return {"Tone": list(struct.unpack("<4d", v.raw))}
        return {"class": v.cls, "hex": v.raw.hex()}
    if isinstance(v, list):
        return [to_plain(x) for x in v]
    if isinstance(v, (bool, int, float)) or v is None:
        return v
    raise TypeError("no plain form for %r" % (v,))


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    data = Path(__file__).resolve().parents[2] / "game" / "Data" / ("Map%03d.rxdata" % int(argv[1]))
    event = loads(data.read_bytes()).ivars["@events"][int(argv[2])]
    print(json.dumps(to_plain(event), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
