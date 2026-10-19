#===============================================================================
# Battle screen at 480x320 (single and double battles).
# Essentials lays the battle out for 512x384: the scene above a 96-pixel
# message bar. Here the scene is 224 pixels tall instead of 288 and 32 pixels
# narrower, so the battler bases move with the screen and the 512-wide boxes
# are narrowed in code (no new art).
#===============================================================================
class Battle::Scene
  # Essentials' formulas evaluated for 480x320, with adjustments for the
  # shorter, narrower scene and the Generation 9 Pack's sprites (D-044):
  # - the player's side moves left by half the lost width (its databoxes moved
  #   left by all of it) and up, so its back sprites show above the message bar;
  # - the foe's side sits as low as the player's databox allows: in a single
  #   battle the one databox drops into the free strip above the message bar;
  #   in a double battle the foes are raised so their feet clear the player's
  #   two databoxes.
  PLAYER_SIDE_SHIFT_X = PSC::Screen::WIDTH_LOST / 2
  PLAYER_SIDE_LIFT_Y  = 16
  FOE_SIDE_LIFT_Y     = 24   # double battles only
  PSC::Screen.redefine(self, :PLAYER_BASE_X, 128 - PLAYER_SIDE_SHIFT_X)
  PSC::Screen.redefine(self, :PLAYER_BASE_Y, Settings::SCREEN_HEIGHT - 80 - PLAYER_SIDE_LIFT_Y)
  PSC::Screen.redefine(self, :FOE_BASE_X, Settings::SCREEN_WIDTH - 128)
  PSC::Screen.redefine(self, :FOE_BASE_Y, (Settings::SCREEN_HEIGHT * 3 / 4) - 112)

  # Double battles: Essentials spaces each side's two battlers 80 pixels apart,
  # which on this narrower scene put the player's lead almost on top of its
  # ally, and puts the player's second battler 16 pixels lower, behind the
  # message bar. Spread both sides further apart and level the player's pair.
  DOUBLE_SPREAD_X = [8, 8, 48, -16]
  DOUBLE_SPREAD_Y = [0, 0, -16, 0]

  # How many battlers the foe's side has in the battle being set up; the
  # backdrop's base and the trainers use the same positions as the battlers.
  @psc_foe_side_size = 1
  class << self
    attr_accessor :psc_foe_side_size

    def psc_foe_lift
      return (@psc_foe_side_size || 1) > 1 ? FOE_SIDE_LIFT_Y : 0
    end

    alias psc_screen_pbBattlerPosition pbBattlerPosition
    def pbBattlerPosition(index, sideSize = 1)
      ret = psc_screen_pbBattlerPosition(index, sideSize)
      if sideSize == 2
        ret[0] += DOUBLE_SPREAD_X[index]
        ret[1] += DOUBLE_SPREAD_Y[index]
      end
      ret[1] -= psc_foe_lift if index.odd?
      return ret
    end

    alias psc_screen_pbTrainerPosition pbTrainerPosition
    def pbTrainerPosition(side, index = 0, sideSize = 1)
      ret = psc_screen_pbTrainerPosition(side, index, sideSize)
      ret[1] -= psc_foe_lift if side == 1
      return ret
    end
  end

  # overlay_message.png is one 512-wide box; its middle is plain fill.
  MESSAGE_BOX_CUT_X = 240

  alias psc_screen_pbInitSprites pbInitSprites
  def pbInitSprites
    Battle::Scene.psc_foe_side_size = @battle.sideSizes[1]
    psc_screen_pbInitSprites
    box = @sprites["messageBox"]
    return if !box&.bitmap || box.bitmap.width <= Graphics.width
    box.psc_replace_bitmap(
      PSC::Screen.squeeze_bitmap(box.bitmap, MESSAGE_BOX_CUT_X, box.bitmap.width - Graphics.width)
    )
  end
end

#-------------------------------------------------------------------------------
# The player's databox in a single battle: Essentials leaves a 12-pixel strip
# between it and the message bar; drop it into the strip so the foe can stand
# lower (see FOE_BASE_Y).
#-------------------------------------------------------------------------------
class Battle::Scene::PokemonDataBox
  MESSAGE_BAR_HEIGHT = 96
  alias psc_screen_initializeDataBoxGraphic initializeDataBoxGraphic
  def initializeDataBoxGraphic(sideSize)
    psc_screen_initializeDataBoxGraphic(sideSize)
    return if sideSize != 1 || @battler.index.odd? || !@databoxBitmap
    @spriteY = Graphics.height - MESSAGE_BAR_HEIGHT - @databoxBitmap.height
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

#-------------------------------------------------------------------------------
# Battler sprites (D-044: the Generation 9 Pack's set). Its front sprites draw
# each art pixel 2x2 (192 px), its back sprites 3x3 (288 px), sized for a
# 288-pixel scene. On our 224-pixel scene a back sprite covered a third of the
# screen and, in doubles, hid its ally. Back sprites are shrunk to 2x2 pixels:
# keep two of every three rows and columns, which is exact for 3x pixel art
# (no blur), so both sides share one pixel size. Done on the bitmap, not with
# zoom, because the send-out animation sets the sprite's zoom itself.
#-------------------------------------------------------------------------------
class Battle::Scene::BattlerSprite
  BACK_ART_SCALE   = 3   # screen pixels per art pixel in the pack's back sprites
  BATTLE_ART_SCALE = 2   # screen pixels per art pixel wanted (the front sprites' size)
  PACK_BACK_SIZE   = 288 # the pack's back sprite canvas (96 art pixels at 3x); others are left alone

  # Stands in for the AnimatedBitmap: the same interface BattlerSprite uses,
  # serving a shrunk copy of the current frame.
  class PscShrunkBitmap
    def initialize(animated)
      @animated = animated
      @source = nil
      @bitmap = nil
    end

    def bitmap
      src = @animated.bitmap
      return nil if !src
      if !src.equal?(@source)
        @bitmap&.dispose
        @bitmap = PscShrunkBitmap.shrink(src)
        @source = src
      end
      return @bitmap
    end

    def width;  return bitmap ? bitmap.width : 0;  end
    def height; return bitmap ? bitmap.height : 0; end
    def update; @animated.update; end

    def dispose
      @animated.dispose
      @bitmap&.dispose
      @bitmap = nil
    end

    def disposed?; return @animated.disposed?; end

    # Source pixel kept for output pixel i: art pixel i / 2, its first or second pixel.
    def self.source_index(i)
      return ((i / BATTLE_ART_SCALE) * BACK_ART_SCALE) + (i % BATTLE_ART_SCALE)
    end

    def self.shrink(src)
      w = src.width * BATTLE_ART_SCALE / BACK_ART_SCALE
      h = src.height * BATTLE_ART_SCALE / BACK_ART_SCALE
      cols = Bitmap.new(w, src.height)
      w.times { |x| cols.blt(x, 0, src, Rect.new(source_index(x), 0, 1, src.height)) }
      ret = Bitmap.new(w, h)
      h.times { |y| ret.blt(0, y, cols, Rect.new(0, source_index(y), w, 1)) }
      cols.dispose
      return ret
    end
  end

  alias psc_screen_setPokemonBitmap setPokemonBitmap
  def setPokemonBitmap(pkmn, back = false)
    psc_screen_setPokemonBitmap(pkmn, back)
    return if !back || !@_iconBitmap || @_iconBitmap.height != PACK_BACK_SIZE
    @_iconBitmap = PscShrunkBitmap.new(@_iconBitmap)
    self.bitmap = @_iconBitmap.bitmap
    pbSetPosition
  end

  # The pack's metrics place its back sprites at full size; shrink their offset
  # with the sprite (Essentials adds BackSprite x/y doubled, see SpeciesMetrics).
  alias psc_screen_pbSetPosition pbSetPosition
  def pbSetPosition
    psc_screen_pbSetPosition
    return if !@_iconBitmap.is_a?(PscShrunkBitmap) || !@pkmn
    offset = GameData::SpeciesMetrics.get_species_form(@pkmn.species, @pkmn.form).back_sprite
    lost = BACK_ART_SCALE - BATTLE_ART_SCALE
    self.x -= offset[0] * 2 * lost / BACK_ART_SCALE
    self.y -= offset[1] * 2 * lost / BACK_ART_SCALE
  end
end
