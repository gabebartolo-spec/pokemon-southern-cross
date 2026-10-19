#===============================================================================
# PSC_Difficulty: engine adapters for hard/normal mode and level caps
# (D-008, D-021, D-022). Each hook is an alias chain around one Essentials
# method or item handler and asks PSC::Rules (lib/psc_rules.rb) for the
# decision; no Essentials method is redefined whole.
#===============================================================================
module PSC
  module Difficulty
    # Written by tools/validate/content.py --emit-caps from content/progression.json.
    CAPS_PATH    = "Data/psc_caps.json"
    RARE_CANDIES = [:RARECANDY]
    EXP_CANDIES  = [:EXPCANDYXS, :EXPCANDYS, :EXPCANDYM, :EXPCANDYL, :EXPCANDYXL]
    # Battle side indices, as Battle::AI#create_ai_objects uses them.
    OPPOSING_SIDE = 1

    module_function

    def mode
      return PSC::Rules.mode_from_save($PokemonGlobal&.psc_mode)
    end

    # Loads the caps table once. A missing or malformed file stops the game with the fix,
    # instead of silently playing hard mode without caps.
    def caps
      return @caps if @caps
      text = pbGetFileString(CAPS_PATH)
      raise "#{CAPS_PATH} is missing; run tools/validate/content.py --emit-caps" if !text
      @caps = PSC::Rules.parse_caps(text)
      PSC::Rules.caps = @caps
      return @caps
    end

    # The current level cap, or nil (normal mode, no player yet, or no gym left).
    def cap
      return nil if !$player
      return PSC::Rules.cap_for(badges: $player.badge_count, mode: mode, caps: caps)
    end

    def at_cap?(pkmn)
      return !PSC::Rules.item_level_up_allowed?(level: pkmn.level, cap: cap)
    end

    def cap_message(pkmn)
      return _INTL("{1} can't grow any stronger until the next badge.", pkmn.name)
    end

    # The part of an Exp gain that fits under the cap, for a Pokemon on growth_rate with exp_now.
    def capped_exp(growth_rate, exp_now, gain)
      c = cap
      return gain if c.nil? || gain <= 0
      return PSC::Rules.exp_after_cap(level: growth_rate.level_from_exp(exp_now), exp_gain: gain,
                                      cap: c, exp_to_cap: growth_rate.minimum_exp_for_level(c) - exp_now)
    end

    # Normal mode: a trainer's Pokemon keeps no held item and no EVs (D-021).
    def trim(pkmn)
      data = PSC::Rules.trim_for_mode({ item: pkmn.item_id, ev: pkmn.ev.clone }, mode: mode)
      pkmn.item = data[:item]
      data[:ev].each { |stat, value| pkmn.ev[stat] = value }
      pkmn.calc_stats
    end

    # Rare Candy and Exp Candies are refused at the cap (and not used up); Rare Candies offer
    # only as many at once as fit under the cap.
    def wrap_level_items
      (RARE_CANDIES + EXP_CANDIES).each do |item|
        use = ItemHandlers::UseOnPokemon[item]
        next if !use
        ItemHandlers::UseOnPokemon.add(item, proc { |itm, qty, pkmn, scene|
          if PSC::Difficulty.at_cap?(pkmn)
            scene.pbDisplay(PSC::Difficulty.cap_message(pkmn))
            next false
          end
          next use.call(itm, qty, pkmn, scene)
        })
      end
      RARE_CANDIES.each do |item|
        most = ItemHandlers::UseOnPokemonMaximum[item]
        next if !most
        ItemHandlers::UseOnPokemonMaximum.add(item, proc { |itm, pkmn|
          next PSC::Rules.level_ups_allowed(level: pkmn.level, cap: PSC::Difficulty.cap,
                                            wanted: most.call(itm, pkmn))
        })
      end
    end
  end
end

# The mode chosen at new game. nil in saves from before this plugin: PSC::Rules reads that as hard.
class PokemonGlobalMetadata
  attr_accessor :psc_mode
end

# The intro event calls this once, after Professor Acacia's welcome (docs/region/STORY.md,
# slice scene 1). The choice is made once and never changed: later calls return the saved mode.
def pbPscChooseDifficulty(prompt = nil)
  return PSC::Difficulty.mode if !$PokemonGlobal.psc_mode.nil?
  commands = [_INTL("Normal: a friendlier road"), _INTL("Hard: every trainer plays to win")]
  prompt ||= _INTL("Before we start, tell me how you like your road.")
  hard_index = commands.length - 1
  choice = pbMessage(prompt, commands, 0, nil, hard_index)   # 0: cannot cancel; cursor on Hard
  $PokemonGlobal.psc_mode = (choice == hard_index) ? PSC::Rules::HARD : PSC::Rules::NORMAL
  return $PokemonGlobal.psc_mode
end

# Battle Exp: a Pokemon at the cap gains none and says so.
class Battle
  alias_method :psc_difficulty_pbGainExpOne, :pbGainExpOne unless method_defined?(:psc_difficulty_pbGainExpOne)

  def pbGainExpOne(idxParty, defeatedBattler, numPartic, expShare, expAll, showMessages = true)
    pkmn = pbParty(0)[idxParty]
    if PSC::Difficulty.at_cap?(pkmn)
      pkmn.calc_stats   # EVs from this foe still count, as Essentials does at max level
      pbDisplayPaused(PSC::Difficulty.cap_message(pkmn)) if showMessages
      return
    end
    psc_difficulty_pbGainExpOne(idxParty, defeatedBattler, numPartic, expShare, expAll, showMessages)
  end
end

# Battle Exp below the cap: the gain stops exactly at the cap level (pbGainExpOne adds Exp here).
module GameData
  class GrowthRate
    alias_method :psc_difficulty_add_exp, :add_exp unless method_defined?(:psc_difficulty_add_exp)

    def add_exp(exp1, exp2)
      return psc_difficulty_add_exp(exp1, PSC::Difficulty.capped_exp(self, exp1, exp2))
    end
  end

  # Normal mode trims trainers' Pokemon after Essentials builds them.
  class Trainer
    alias_method :psc_difficulty_to_trainer, :to_trainer unless method_defined?(:psc_difficulty_to_trainer)

    def to_trainer
      trainer = psc_difficulty_to_trainer
      trainer.party.each { |pkmn| PSC::Difficulty.trim(pkmn) }
      return trainer
    end
  end
end

# Exp Candies below the cap: the Exp stops at the cap level.
alias psc_difficulty_pbChangeExp pbChangeExp unless Object.private_method_defined?(:psc_difficulty_pbChangeExp)

def pbChangeExp(pkmn, new_exp, scene)
  gain = PSC::Difficulty.capped_exp(pkmn.growth_rate, pkmn.exp, new_exp - pkmn.exp)
  psc_difficulty_pbChangeExp(pkmn, pkmn.exp + gain, scene)
end

# Day Care Exp stops at the cap too.
class DayCare
  class DayCareSlot
    alias_method :psc_difficulty_add_exp, :add_exp unless method_defined?(:psc_difficulty_add_exp)

    def add_exp(amount = 1)
      amount = PSC::Difficulty.capped_exp(@pokemon.growth_rate, @pokemon.exp, amount) if filled?
      return if amount <= 0
      psc_difficulty_add_exp(amount)
    end
  end
end

# Normal mode halves the opposing trainers' AI skill (D-021).
class Battle::AI::AITrainer
  alias_method :psc_difficulty_set_up_skill, :set_up_skill unless method_defined?(:psc_difficulty_set_up_skill)

  def set_up_skill
    psc_difficulty_set_up_skill
    return if !@trainer || @side != PSC::Difficulty::OPPOSING_SIDE
    @skill = PSC::Rules.ai_skill(@skill, mode: PSC::Difficulty.mode)
  end
end

# The pause menu shows the cap on hard ("Level cap: 15"); Safari and Bug Contest keep their own info.
class PokemonPauseMenu
  alias_method :psc_difficulty_pbShowInfo, :pbShowInfo unless method_defined?(:psc_difficulty_pbShowInfo)

  def pbShowInfo
    psc_difficulty_pbShowInfo
    return if pbInSafari? || pbInBugContest?
    cap = PSC::Difficulty.cap
    @scene.pbShowInfo(_INTL("Level cap: {1}", cap)) if cap
  end
end

PSC::Difficulty.wrap_level_items
