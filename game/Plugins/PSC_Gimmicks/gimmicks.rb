#===============================================================================
# PSC_Gimmicks: Mega Evolution is the only battle gimmick (D-011), with classic
# Generation 9 rules (director, 2026-10-19).
#
# Terastal, Dynamax and Z-Moves are not part of Essentials v21.1 or of the
# Generation 9 Pack; each would arrive as its own plugin. GIMMICK_PLUGINS names
# those plugins, and loading the game with one installed stops with the fix.
# tests/python/test_gimmicks.py checks the same thing in CI.
#
# Loads after the Generation 9 Pack (meta.txt Requires), so the override below
# replaces the pack's own setting without editing the pack.
#===============================================================================
module Settings
  # The pack ships CHAMPIONS_MECHANICS = true (Pokemon Champions status, ability
  # and move rules). Classic Gen 9 rules: off. Every use reads it at battle time.
  remove_const(:CHAMPIONS_MECHANICS) if const_defined?(:CHAMPIONS_MECHANICS, false)
  CHAMPIONS_MECHANICS = false
end

module PSC
  module Gimmicks
    # Plugin names (meta.txt Name) that add Terastal, Dynamax or Z-Moves.
    GIMMICK_PLUGINS = [
      "[DBK] Terastallization", "[DBK] Dynamax", "[DBK] Z-Power",
      "Terastal Phenomenon", "ZUD Mechanics", "ZUD Plugin"
    ]

    module_function

    def installed_gimmick_plugins
      return GIMMICK_PLUGINS.select { |name| PluginManager.installed?(name) }
    end
  end
end

bad = PSC::Gimmicks.installed_gimmick_plugins
if !bad.empty?
  raise "Mega Evolution is the only battle gimmick (D-011). Remove from Plugins/: #{bad.join(', ')}"
end
