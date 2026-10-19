#===============================================================================
# Battle screen at 480x320 (single and double battles).
# Essentials lays the battle out for 512x384: the scene above a 96-pixel
# message bar. Here the scene is 224 pixels tall instead of 288 and 32 pixels
# narrower, so the battler bases move with the screen and the 512-wide boxes
# are narrowed in code (no new art).
#===============================================================================
class Battle::Scene
  # Essentials' formulas evaluated for 480x320, with two adjustments for the
  # shorter, narrower scene: the player's side moves left by half the lost
  # width (its databoxes moved left by all of it), and the foe's side is raised
  # so the foes' feet clear the player's databoxes in a double battle.
  PLAYER_SIDE_SHIFT_X = PSC::Screen::WIDTH_LOST / 2
  FOE_SIDE_LIFT_Y     = 24
  PSC::Screen.redefine(self, :PLAYER_BASE_X, 128 - PLAYER_SIDE_SHIFT_X)
  PSC::Screen.redefine(self, :PLAYER_BASE_Y, Settings::SCREEN_HEIGHT - 80)
  PSC::Screen.redefine(self, :FOE_BASE_X, Settings::SCREEN_WIDTH - 128)
  PSC::Screen.redefine(self, :FOE_BASE_Y, (Settings::SCREEN_HEIGHT * 3 / 4) - 112 - FOE_SIDE_LIFT_Y)

  # overlay_message.png is one 512-wide box; its middle is plain fill.
  MESSAGE_BOX_CUT_X = 240

  alias psc_screen_pbInitSprites pbInitSprites
  def pbInitSprites
    psc_screen_pbInitSprites
    box = @sprites["messageBox"]
    return if !box&.bitmap || box.bitmap.width <= Graphics.width
    box.psc_replace_bitmap(
      PSC::Screen.squeeze_bitmap(box.bitmap, MESSAGE_BOX_CUT_X, box.bitmap.width - Graphics.width)
    )
  end
end

#-------------------------------------------------------------------------------
# Command menu ("What will X do?" + Fight/Bag/Pokémon/Run). The buttons sit
# 260 pixels from the right edge, so the text box (248 wide in the art) is
# narrowed by the 32 pixels the screen lost, and its text with it.
#-------------------------------------------------------------------------------
class Battle::Scene::CommandMenu
  TEXT_BOX_CUT_X = 100

  alias psc_screen_initialize initialize
  def initialize(viewport, z)
    psc_screen_initialize(viewport, z)
    @msgBox.width -= PSC::Screen::WIDTH_LOST
    bg = @sprites["background"]
    return if !bg&.bitmap
    bg.psc_replace_bitmap(PSC::Screen.squeeze_bitmap(bg.bitmap, TEXT_BOX_CUT_X, PSC::Screen::WIDTH_LOST))
  end
end

#-------------------------------------------------------------------------------
# Fight menu. In the art the four move buttons fill x 4 to 384 and the move
# info box (type and PP) fills 388 to 512. Each button column is narrowed by 16
# pixels (cut from the plain middle of the button), so the buttons end at 356
# and the info box keeps its full width at 356 to 480.
#-------------------------------------------------------------------------------
class Battle::Scene::FightMenu
  BUTTON_CUT       = PSC::Screen::WIDTH_LOST / 2   # per column of buttons
  ART_BUTTON_WIDTH = 192                           # one button in cursor_fight.png
  ART_INFO_LEFT    = 388                           # info box left edge in overlay_fight.png
  INFO_BOX_LEFT    = ART_INFO_LEFT - PSC::Screen::WIDTH_LOST
  INFO_BOX_CENTER_X = (INFO_BOX_LEFT + Settings::SCREEN_WIDTH) / 2
  PP_TEXT_Y        = 56

  alias psc_screen_initialize initialize
  def initialize(viewport, z)
    psc_screen_initialize(viewport, z)
    return if !USE_GRAPHICS
    psc_narrow_background
    psc_narrow_buttons
    @typeIcon.x = self.x + INFO_BOX_CENTER_X - (@typeBitmap.width / 2)
  end

  alias psc_screen_dispose dispose
  def dispose
    psc_screen_dispose
    @psc_button_bitmap&.dispose
  end

  # Cut BUTTON_CUT columns from the middle of each button slot in the background.
  def psc_narrow_background
    bg = @sprites["background"]
    return if !bg&.bitmap || bg.bitmap.width <= Graphics.width
    half = ART_BUTTON_WIDTH / 2
    step1 = PSC::Screen.squeeze_bitmap(bg.bitmap, half, BUTTON_CUT)
    step2 = PSC::Screen.squeeze_bitmap(step1, ART_BUTTON_WIDTH + half - BUTTON_CUT, BUTTON_CUT)
    step1.dispose
    bg.psc_replace_bitmap(step2)
  end

  # The same cut on cursor_fight.png, whose two columns are the unselected and
  # selected button.
  def psc_narrow_buttons
    src = @buttonBitmap.bitmap
    half = ART_BUTTON_WIDTH / 2
    step1 = PSC::Screen.squeeze_bitmap(src, half, BUTTON_CUT)
    @psc_button_bitmap = PSC::Screen.squeeze_bitmap(step1, ART_BUTTON_WIDTH + half - BUTTON_CUT, BUTTON_CUT)
    step1.dispose
    @psc_button_width = ART_BUTTON_WIDTH - BUTTON_CUT
    @buttons.each_with_index do |button, i|
      button.bitmap = @psc_button_bitmap
      button.src_rect.width = @psc_button_width
      button.x = self.x + 4 + (i.even? ? 0 : @psc_button_width - 4)
    end
  end

  # Essentials' refreshSelection, using the narrowed button width.
  alias psc_screen_refreshSelection refreshSelection
  def refreshSelection
    return psc_screen_refreshSelection if !USE_GRAPHICS || !@psc_button_width
    moves = (@battler) ? @battler.moves : []
    @buttons.each_with_index do |button, i|
      if !moves[i]
        @visibility["button_#{i}"] = false
        next
      end
      @visibility["button_#{i}"] = true
      button.src_rect.x = (i == @index) ? @psc_button_width : 0
      button.src_rect.y = GameData::Type.get(moves[i].display_type(@battler)).icon_position * BUTTON_HEIGHT
      button.z          = self.z + ((i == @index) ? 4 : 3)
    end
    refreshMoveData(moves[@index])
  end

  # Essentials' refreshMoveData, with the PP text centred in the info box.
  alias psc_screen_refreshMoveData refreshMoveData
  def refreshMoveData(move)
    return psc_screen_refreshMoveData(move) if !USE_GRAPHICS
    @infoOverlay.bitmap.clear
    if !move
      @visibility["typeIcon"] = false
      return
    end
    @visibility["typeIcon"] = true
    type_number = GameData::Type.get(move.display_type(@battler)).icon_position
    @typeIcon.src_rect.y = type_number * TYPE_ICON_HEIGHT
    return if move.total_pp <= 0
    ppFraction = [(4.0 * move.pp / move.total_pp).ceil, 3].min
    pbDrawTextPositions(@infoOverlay.bitmap,
                        [[_INTL("PP: {1}/{2}", move.pp, move.total_pp), INFO_BOX_CENTER_X, PP_TEXT_Y, :center,
                          PP_COLORS[ppFraction * 2], PP_COLORS[(ppFraction * 2) + 1]]])
  end
end

#-------------------------------------------------------------------------------
# Target menu (double battles). Essentials centres the buttons on a 512-wide
# screen; move them left by half the lost width so they centre on 480.
#-------------------------------------------------------------------------------
class Battle::Scene::TargetMenu
  alias psc_screen_initialize initialize
  def initialize(viewport, z, sideSizes)
    psc_screen_initialize(viewport, z, sideSizes)
    @buttons.each { |button| button.x -= PSC::Screen::WIDTH_LOST / 2 if button }
  end
end

#-------------------------------------------------------------------------------
# Ability splash bar: the player's side sat 180 pixels down a 288-pixel scene;
# move it up by the height the screen lost so it stays above the message bar.
#-------------------------------------------------------------------------------
class Battle::Scene::AbilitySplashBar
  alias psc_screen_initialize initialize
  def initialize(side, viewport = nil)
    psc_screen_initialize(side, viewport)
    self.y -= PSC::Screen::HEIGHT_LOST if side == 0
  end
end
