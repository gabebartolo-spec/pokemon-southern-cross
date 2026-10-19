require "minitest/autorun"

# Real Ruby Marshal must load what tools/maps/build.py writes. Minimal stand-ins for the RGSS
# classes; user-dumped Table/Tone/Color unpack their bytes as RGSS does.
module RPG
  class Map; attr_reader :width, :height, :data, :events, :tileset_id; end
  class MapInfo; attr_reader :name, :parent_id, :order; end
  class Event
    attr_reader :pages, :name, :x, :y, :id
    class Page
      class Condition; end
      class Graphic; end
    end
  end
  class EventCommand; end
  class MoveRoute; end
  class MoveCommand; end
  class AudioFile; end
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
    assert_equal 0, m.events.size     # its only object is a spawn, which builds no event
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

  def test_base_map_with_events_loads_with_the_same_stubs
    m = load("Map003.rxdata")
    assert_equal 14, m.events.size
    assert_kind_of RPG::Event::Page, m.events.values.first.pages.first
  end
end
