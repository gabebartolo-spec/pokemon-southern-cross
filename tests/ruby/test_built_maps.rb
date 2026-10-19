require "minitest/autorun"

# Real Ruby Marshal must load what tools/maps/build.py writes. Minimal stand-ins for the RGSS
# classes; user-dumped Table/Tone/Color unpack their bytes as RGSS does.
module RPG
  class Map; attr_reader :width, :height, :data, :events, :tileset_id; end
  class MapInfo; attr_reader :name, :parent_id, :order; end
  class Event
    attr_reader :pages, :name, :x, :y, :id
    class Page
      attr_reader :list, :trigger, :condition, :graphic
      class Condition; attr_reader :self_switch_valid, :self_switch_ch; end
      class Graphic; attr_reader :character_name, :direction; end
    end
  end
  class EventCommand; attr_reader :code, :parameters, :indent; end
  class MoveRoute; end
  class MoveCommand; end
  class AudioFile; attr_reader :name, :volume, :pitch; end
  class Tileset; attr_reader :id, :name, :passages; end
end

class Table
  attr_reader :xsize, :ysize, :zsize, :data
  def self._load(bytes)
    _dim, x, y, z, n = bytes.unpack("l<5")
    t = allocate
    t.instance_variable_set(:@xsize, x)
    t.instance_variable_set(:@ysize, y)
    t.instance_variable_set(:@zsize, z)
    t.instance_variable_set(:@data, bytes[20, n * 2].unpack("s<*"))
    t
  end

  def [](x, y = 0, z = 0)
    @data[x + y * @xsize + z * @xsize * @ysize]
  end
end

class Tone
  attr_reader :rgbg
  def self._load(bytes) = allocate.tap { |t| t.instance_variable_set(:@rgbg, bytes.unpack("E4")) }
end

class Color
  def self._load(bytes) = allocate.tap { |c| c.instance_variable_set(:@rgba, bytes.unpack("E4")) }
end

class TestBuiltMaps < Minitest::Test
  DATA = File.expand_path("../../game/Data", __dir__)

  def load(name) = File.open(File.join(DATA, name), "rb") { |f| Marshal.load(f) }

  def test_map900_loads_with_its_size_and_tiles
    m = load("Map900.rxdata")
    assert_kind_of RPG::Map, m
    assert_equal [32, 21], [m.width, m.height]
    assert_equal [32, 21, 3], [m.data.xsize, m.data.ysize, m.data.zsize]
    assert_equal 32 * 21 * 3, m.data.data.size
    assert_equal 385, m.data[9, 9, 0] # the one tile changed from the Lappet Town copy
    assert_equal 7, m.events.size     # eight objects; the spawn builds no event
    assert_equal 1, m.tileset_id
  end

  def test_mapinfos_holds_ours_and_base
    infos = load("MapInfos.rxdata")
    assert_equal "Builder test", infos[900].name
    assert_equal Encoding::UTF_8, infos[900].name.encoding
    assert_equal "Lappet Town", infos[2].name
    assert_equal 0, infos[900].parent_id
  end

  def test_tilesets_load
    sets = load("Tilesets.rxdata")
    assert_nil sets[0]
    assert_equal 26, sets.size
    assert_equal "Outside", sets[1].name
    assert_equal 4400, sets[1].passages.data.size
  end

  # Map900's events, one of each object type (content/maps/900_builder_test.tmj), by name.
  def events900 = load("Map900.rxdata").events.values.to_h { |e| [e.name, e] }

  def codes(page) = page.list.map(&:code)

  def test_map900_holds_one_event_of_each_type
    evs = load("Map900.rxdata").events
    assert_equal((1..7).to_a, evs.keys.sort)
    assert_equal %w[Door Sign Local Potion Trainer(3) Trainer(2) Chime], evs.keys.sort.map { |k| evs[k].name }
    evs.each { |k, e| assert_equal k, e.id }
    assert_equal [8, 7], [evs[1].x, evs[1].y]
  end

  def test_warp_event_fades_and_transfers
    page = events900["Door"].pages.first
    assert_equal 1, page.trigger
    assert_equal [250, 223, 106, 201, 223, 0], codes(page)
    assert_equal "Door exit", page.list[0].parameters[0].name
    assert_equal [-255.0, -255.0, -255.0, 0.0], page.list[1].parameters[0].rgbg
    assert_equal 6, page.list[1].parameters[1]
    assert_equal [0, 2, 8, 7, 2, 1], page.list[3].parameters
  end

  def test_sign_and_npc_show_their_text
    sign = events900["Sign"].pages.first
    assert_equal [0, [101, 401, 0]], [sign.trigger, codes(sign)]
    assert_equal ["Builder test map."], sign.list[0].parameters
    assert_equal Encoding::UTF_8, sign.list[0].parameters[0].encoding
    assert_equal "", sign.graphic.character_name
    npc = events900["Local"].pages.first
    assert_equal [101, 101, 0], codes(npc)
    assert_equal ["NPC 01", 4], [npc.graphic.character_name, npc.graphic.direction]
    assert_equal ["G'day."], npc.list[0].parameters
  end

  def test_item_ball_gives_the_item_once
    first, taken = events900["Potion"].pages
    assert_equal "Object ball", first.graphic.character_name
    assert_equal [111, 123, 0, 412, 0], codes(first)
    assert_equal [12, "pbItemBall(:POTION)"], first.list[0].parameters
    assert_equal [["A", 0], 1], [first.list[1].parameters, first.list[1].indent]
    assert_equal [true, "A", ""], [taken.condition.self_switch_valid, taken.condition.self_switch_ch,
                                   taken.graphic.character_name]
  end

  def test_trainers_battle_then_switch_to_their_after_page
    battle, after = events900["Trainer(3)"].pages
    assert_equal [2, false], [battle.trigger, battle.condition.self_switch_valid]
    assert_equal [355, 355, 101, 111, 123, 0, 412, 355, 0], codes(battle)
    assert_equal ["pbTrainerIntro(:YOUNGSTER)"], battle.list[0].parameters
    assert_equal [12, 'TrainerBattle.start(:YOUNGSTER, "Ben")'], battle.list[3].parameters
    assert_equal ["trainer_YOUNGSTER", 6], [battle.graphic.character_name, battle.graphic.direction]
    assert_equal [0, true, ["Good battle, that."]], [after.trigger, after.condition.self_switch_valid,
                                                    after.list[0].parameters]
    doubles = events900["Trainer(2)"].pages.first
    assert_equal [355, 355, 101, 355, 111, 123, 0, 412, 355, 0], codes(doubles)
    assert_equal ['setBattleRule("double")'], doubles.list[3].parameters
    assert_equal [12, 'TrainerBattle.start(:LASS, "Crissy")'], doubles.list[4].parameters
  end

  def test_script_event_runs_its_script
    page = events900["Chime"].pages.first
    assert_equal [0, [355, 0]], [page.trigger, codes(page)]
    assert_equal ['pbSEPlay("Door exit")'], page.list[0].parameters
  end

  def test_base_map_with_events_loads_with_the_same_stubs
    m = load("Map003.rxdata")
    assert_equal 14, m.events.size
    assert_kind_of RPG::Event::Page, m.events.values.first.pages.first
  end
end
