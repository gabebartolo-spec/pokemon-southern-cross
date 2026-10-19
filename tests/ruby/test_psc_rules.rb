require "minitest/autorun"
require File.expand_path("../../game/Plugins/PSC_Difficulty/lib/psc_rules.rb", __dir__)

# PSC::Rules is the pure half of the PSC_Difficulty plugin: no Essentials constants, so plain Ruby
# loads it here. The engine adapters (difficulty.rb) only call these functions.
class TestPscRules < Minitest::Test
  CAPS = { 0 => 15, 1 => 21 }.freeze

  # Medium Fast growth: the minimum Exp for level n is n**3.
  def exp_for(level) = level**3

  def test_cap_nil_on_normal
    assert_nil PSC::Rules.cap_for(badges: 0, mode: :normal, caps: CAPS)
  end

  def test_cap_on_hard_follows_badges
    assert_equal 15, PSC::Rules.cap_for(badges: 0, mode: :hard, caps: CAPS)
    assert_equal 21, PSC::Rules.cap_for(badges: 1, mode: :hard, caps: CAPS)
    assert_nil PSC::Rules.cap_for(badges: 2, mode: :hard, caps: CAPS) # no later gym: no cap
  end

  def test_cap_uses_the_loaded_table_by_default
    PSC::Rules.caps = { 0 => 14 }
    assert_equal 14, PSC::Rules.cap_for(badges: 0, mode: :hard)
  ensure
    PSC::Rules.caps = {}
  end

  def test_exp_zero_at_cap
    assert_equal 0, PSC::Rules.exp_after_cap(level: 15, exp_gain: 500, cap: 15)
    assert_equal 0, PSC::Rules.exp_after_cap(level: 17, exp_gain: 500, cap: 15)
  end

  def test_exp_unchanged_without_a_cap
    assert_equal 500, PSC::Rules.exp_after_cap(level: 60, exp_gain: 500, cap: nil)
  end

  def test_exp_clamped_to_cap_boundary
    exp_now = 3_000 # level 14 (14**3 = 2744 <= 3000 < 3375 = 15**3)
    gain = PSC::Rules.exp_after_cap(level: 14, exp_gain: 1_000, cap: 15,
                                    exp_to_cap: exp_for(15) - exp_now)
    assert_equal 375, gain
    assert_equal exp_for(15), exp_now + gain # lands exactly on level 15, not one point past it
    assert_equal 200, PSC::Rules.exp_after_cap(level: 14, exp_gain: 200, cap: 15,
                                               exp_to_cap: exp_for(15) - exp_now)
  end

  def test_rare_candy_blocked_at_cap
    refute PSC::Rules.item_level_up_allowed?(level: 15, cap: 15)
    assert PSC::Rules.item_level_up_allowed?(level: 14, cap: 15)
    assert PSC::Rules.item_level_up_allowed?(level: 99, cap: nil)
  end

  def test_level_ups_allowed_stop_at_cap
    assert_equal 1, PSC::Rules.level_ups_allowed(level: 14, cap: 15, wanted: 5)
    assert_equal 0, PSC::Rules.level_ups_allowed(level: 16, cap: 15, wanted: 5)
    assert_equal 5, PSC::Rules.level_ups_allowed(level: 14, cap: nil, wanted: 5)
  end

  def test_trim_strips_items_and_evs_on_normal
    pkmn = { species: :TREECKO, item: :ORANBERRY, ev: { HP: 21, ATTACK: 21, SPEED: 0 } }
    trimmed = PSC::Rules.trim_for_mode(pkmn, mode: :normal)
    assert_nil trimmed[:item]
    assert_equal({ HP: 0, ATTACK: 0, SPEED: 0 }, trimmed[:ev])
    assert_equal :TREECKO, trimmed[:species]
    assert_equal :ORANBERRY, pkmn[:item] # the input is not changed
    assert_equal pkmn, PSC::Rules.trim_for_mode(pkmn, mode: :hard)
  end

  def test_ai_skill_halved_on_normal
    assert_equal 50, PSC::Rules.ai_skill(100, mode: :normal)
    assert_equal 15, PSC::Rules.ai_skill(31, mode: :normal)
    assert_equal 100, PSC::Rules.ai_skill(100, mode: :hard)
  end

  def test_ai_skill_on_normal_never_drops_a_trainer_to_wild_play
    assert_equal 1, PSC::Rules.ai_skill(1, mode: :normal)
    assert_equal 1, PSC::Rules.ai_skill(3, mode: :normal)
    assert_equal 0, PSC::Rules.ai_skill(0, mode: :normal) # skill 0 stays 0, it is not raised
  end

  # Essentials v21.1's UseOnPokemonMaximum formula for every Exp Candy (Item_Effects).
  def candies_offered(pkmn, gain) = ((pkmn.growth_rate.maximum_exp - pkmn.exp) / gain.to_f).ceil

  def test_exp_candy_count_stops_at_the_candy_that_reaches_the_cap
    exp_now = 3_000 # level 14; cap 15 starts at 15**3 = 3375, 375 Exp away
    stand_in = PSC::Rules.candy_stand_in(exp: exp_now, exp_at_cap: exp_for(15))
    assert_equal 4, candies_offered(stand_in, 100)    # XS: 300 falls short, the 4th reaches the cap
    assert_equal 1, candies_offered(stand_in, 800)    # S
    assert_equal 1, candies_offered(stand_in, 30_000) # XL
    assert_equal 0, candies_offered(PSC::Rules.candy_stand_in(exp: exp_for(15), exp_at_cap: exp_for(15)), 100)
  end

  def test_mode_defaults_to_hard_when_missing_from_save
    assert_equal :hard, PSC::Rules.mode_from_save(nil)
    assert_equal :hard, PSC::Rules.mode_from_save(:easy)
    assert_equal :hard, PSC::Rules.mode_from_save(3)
    assert_equal :hard, PSC::Rules.mode_from_save(:hard)
    assert_equal :normal, PSC::Rules.mode_from_save(:normal)
    assert_equal :normal, PSC::Rules.mode_from_save("normal")
  end

  def test_parse_caps_reads_the_emitted_file
    assert_equal({ 0 => 14, 1 => 20 }, PSC::Rules.parse_caps(%({"0": 14, "1": 20}\n)))
    assert_equal({}, PSC::Rules.parse_caps("{}"))
    assert_raises(ArgumentError) { PSC::Rules.parse_caps(%({"0": "fourteen"})) }
  end

  def test_repo_caps_file_parses
    path = File.expand_path("../../game/Data/psc_caps.json", __dir__)
    caps = PSC::Rules.parse_caps(File.read(path))
    refute_empty caps
    assert(caps.all? { |badges, cap| badges.is_a?(Integer) && cap.is_a?(Integer) })
  end
end
