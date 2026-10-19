#===============================================================================
# Load screen (Continue / New Game / Options) at 480x320. Essentials centres
# its panels and the Continue panel's player and party icons on a 512-wide
# screen; move them left by half the lost width so they centre on 480.
#===============================================================================
class PokemonLoad_Scene
  SHIFT_X = PSC::Screen::WIDTH_LOST / 2

  alias psc_screen_pbStartScene pbStartScene
  def pbStartScene(*args)
    psc_screen_pbStartScene(*args)
    @sprites.each { |key, sprite| sprite.x -= SHIFT_X if key.start_with?("panel") }
  end

  alias psc_screen_pbSetParty pbSetParty
  def pbSetParty(trainer)
    psc_screen_pbSetParty(trainer)
    @sprites.each do |key, sprite|
      sprite.x -= SHIFT_X if key == "player" || key.start_with?("party")
    end
  end
end
