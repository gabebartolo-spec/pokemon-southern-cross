#===============================================================================
# Window size (Options > Screen Size): 1x, 2x, 3x or fullscreen only. The game
# is 480x320 and mkxp.json scales by whole numbers with no smoothing, so the
# half sizes Essentials offers (0.5x, 1.5x) would show a smaller picture
# inside a bigger window. Fullscreen stays: integer scaling letterboxes it.
#
# Sizes keep Essentials' $PokemonSystem.screensize numbers, where the window
# scale is (size + 1) / 2 and 4 means fullscreen; 3x is the new value 5.
#===============================================================================
module PSC
  module Screen
    SIZE_1X      = 1
    SIZE_2X      = 3
    SIZE_FULL    = 4
    SIZE_3X      = 5
    SIZES        = [SIZE_1X, SIZE_2X, SIZE_3X, SIZE_FULL]   # order shown in Options
    DEFAULT_SIZE = SIZE_2X
    # Scales closer than this count as equal (Graphics.scale is a float).
    SCALE_TOLERANCE = 0.01

    def self.allowed_size(size)
      return SIZES.include?(size) ? size : DEFAULT_SIZE
    end

    def self.window_scale(size)
      return (size + 1) * 0.5
    end

    # Sets the window scale and checks it held. mkxp-z 2.4.2: the window change
    # made by the first Graphics.resize_screen lands one frame later and puts
    # Graphics.scale back to 1.0, so the game opened in a 480x320 window
    # (measured 2026-10-19). Later scale changes hold at once (measured 1x, 2x,
    # 3x). So after every change, wait one frame and set the scale again if
    # it moved. Manual re-check item in docs/captures/README.md.
    def self.set_window_scale(scale)
      Graphics.scale = scale
      Graphics.center
      Graphics.update
      return if (Graphics.scale - scale).abs < SCALE_TOLERANCE
      Graphics.scale = scale
      Graphics.center
    end
  end
end

# Replaces Essentials' pbSetResizeFactor (UI_Options/MKXP_Compatibility).
def pbSetResizeFactor(factor)
  # Old saves (or a default) with a size we no longer offer become 2x.
  if $PokemonSystem && !PSC::Screen::SIZES.include?($PokemonSystem.screensize)
    $PokemonSystem.screensize = PSC::Screen::DEFAULT_SIZE
  end
  # Game.set_up_system passes [screensize, 4].min, which would turn 3x into
  # fullscreen; use the stored 3x instead.
  if factor == PSC::Screen::SIZE_FULL && $PokemonSystem&.screensize == PSC::Screen::SIZE_3X
    factor = PSC::Screen::SIZE_3X
  end
  factor = PSC::Screen.allowed_size(factor)
  if !$ResizeInitialized
    Graphics.resize_screen(Settings::SCREEN_WIDTH, Settings::SCREEN_HEIGHT)
    $ResizeInitialized = true
  end
  if factor == PSC::Screen::SIZE_FULL
    Graphics.fullscreen = true if !Graphics.fullscreen
  else
    Graphics.fullscreen = false if Graphics.fullscreen
    PSC::Screen.set_window_scale(PSC::Screen.window_scale(factor))
  end
end

MenuHandlers.add(:options_menu, :screen_size, {
  "name"        => _INTL("Screen Size"),
  "order"       => 120,
  "type"        => EnumOption,
  "parameters"  => [_INTL("1x"), _INTL("2x"), _INTL("3x"), _INTL("Full")],
  "description" => _INTL("Choose the size of the game window."),
  "get_proc"    => proc { next PSC::Screen::SIZES.index(PSC::Screen.allowed_size($PokemonSystem.screensize)) },
  "set_proc"    => proc { |value, _scene|
    size = PSC::Screen::SIZES[value]
    next if $PokemonSystem.screensize == size
    $PokemonSystem.screensize = size
    pbSetResizeFactor(size)
  }
})
