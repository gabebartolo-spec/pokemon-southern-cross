#===============================================================================
# PSC::Rules - the pure rules for difficulty and level caps (D-008, D-021, D-022).
# No Essentials constants: the plugin loads it first (meta.txt Scripts line) and
# tests/ruby/test_psc_rules.rb loads it under plain Ruby. difficulty.rb holds the
# engine adapters, each a few lines calling these functions.
#===============================================================================
module PSC
  module Rules
    HARD   = :hard
    NORMAL = :normal
    # Normal mode keeps every trainer's team but halves the AI's skill (D-021).
    NORMAL_AI_SKILL_DIVISOR = 2
    # The caps file written by tools/validate/content.py --emit-caps: {"<badges>": cap, ...}.
    CAPS_PAIR = /"(\d+)"\s*:\s*(\d+)/
    CAPS_FILE = /\A\s*\{\s*(#{CAPS_PAIR}\s*(,\s*#{CAPS_PAIR}\s*)*)?\}\s*\z/

    @caps = {}

    class << self
      # {badges held => level cap}, loaded by the adapter from game/Data/psc_caps.json.
      attr_reader :caps

      def caps=(table)
        @caps = table || {}
      end

      # Anything but an explicit normal choice is hard, so saves made before this plugin
      # existed (no psc_mode) load as hard.
      def mode_from_save(value)
        return NORMAL if value.to_s == NORMAL.to_s
        return HARD
      end

      # The level cap for this many badges, or nil: normal mode, or no gym left to cap for.
      def cap_for(badges:, mode:, caps: self.caps)
        return nil if mode_from_save(mode) == NORMAL
        return caps[badges]
      end

      # The Exp a Pokemon may still take. At or above the cap: 0. Below it: the gain, cut to
      # exp_to_cap (the Exp still needed to reach the cap level) when that is given.
      def exp_after_cap(level:, exp_gain:, cap:, exp_to_cap: nil)
        return exp_gain if cap.nil?
        return 0 if level >= cap
        return exp_gain if exp_to_cap.nil?
        return [[exp_gain, exp_to_cap].min, 0].max
      end

      # Whether a Rare Candy or an Exp Candy may be used at all.
      def item_level_up_allowed?(level:, cap:)
        return cap.nil? || level < cap
      end

      # How many of the wanted level-ups fit under the cap (Rare Candies at once).
      def level_ups_allowed(level:, cap:, wanted:)
        return wanted if cap.nil?
        return [[wanted, cap - level].min, 0].max
      end

      # A trainer's Pokemon as a hash ({item:, ev: {stat => value}, ...}). Normal mode drops the
      # held item and every EV; hard mode returns it unchanged. The input is never modified.
      def trim_for_mode(pokemon_hash, mode:)
        return pokemon_hash if mode_from_save(mode) == HARD
        evs = (pokemon_hash[:ev] || {}).transform_values { 0 }
        return pokemon_hash.merge(item: nil, ev: evs)
      end

      def ai_skill(base_skill, mode:)
        return base_skill if mode_from_save(mode) == HARD
        return [base_skill / NORMAL_AI_SKILL_DIVISOR, 0].max
      end

      # Parses the caps file text into {Integer badges => Integer cap}. Only the flat shape the
      # emitter writes is accepted, so a hand-edited file fails loudly instead of silently.
      def parse_caps(text)
        raise ArgumentError, "caps file is not {\"<badges>\": <cap>, ...}" if text !~ CAPS_FILE
        return text.scan(CAPS_PAIR).to_h { |badges, cap| [badges.to_i, cap.to_i] }
      end
    end
  end
end
