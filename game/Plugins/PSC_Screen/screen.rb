#===============================================================================
# PSC Screen (D-017): the game runs at 480x320, exactly twice the GBA's 240x160.
# The window opens at 2x (960x640, mkxp.json) with integer scaling and no
# smoothing. Essentials reads Settings::SCREEN_WIDTH/HEIGHT in
# pbSetResizeFactor (Graphics.resize_screen), which runs in Game.set_up_system,
# after plugins load, so overriding the constants here is enough for the screen
# itself. A few constants and viewports were already computed from the old
# 512x384 when Essentials' scripts loaded; they are recomputed below.
#===============================================================================
module PSC
  module Screen
    WIDTH  = 480
    HEIGHT = 320
    # Graphics.scale: 2.0 keeps the window at 960x640 (Options "Screen Size" XL).
    SCALE  = 2.0
    # The screen size Essentials' own layouts and UI bitmaps were drawn for.
    ESSENTIALS_WIDTH  = 512
    ESSENTIALS_HEIGHT = 384
    # How much narrower and shorter our screen is than Essentials' (32 and 64).
    WIDTH_LOST  = ESSENTIALS_WIDTH - WIDTH
    HEIGHT_LOST = ESSENTIALS_HEIGHT - HEIGHT

    def self.redefine(mod, name, value)
      mod.send(:remove_const, name) if mod.const_defined?(name, false)
      mod.const_set(name, value)
    end

    # Returns a new bitmap: src with the columns [cut_x, cut_x + cut_width)
    # removed and the right part moved left. Used to narrow Essentials' 512-wide
    # boxes where their middle is a plain fill. The caller owns the bitmap.
    def self.squeeze_bitmap(src, cut_x, cut_width)
      ret = Bitmap.new(src.width - cut_width, src.height)
      ret.blt(0, 0, src, Rect.new(0, 0, cut_x, src.height))
      ret.blt(cut_x, 0, src, Rect.new(cut_x + cut_width, 0, src.width - cut_x - cut_width, src.height))
      return ret
    end
  end
end

PSC::Screen.redefine(Settings, :SCREEN_WIDTH, PSC::Screen::WIDTH)
PSC::Screen.redefine(Settings, :SCREEN_HEIGHT, PSC::Screen::HEIGHT)
PSC::Screen.redefine(Settings, :SCREEN_SCALE, PSC::Screen::SCALE)

# Game_Player: the camera centre (same formula as Essentials, new size).
PSC::Screen.redefine(Game_Player, :SCREEN_CENTER_X,
                     ((Settings::SCREEN_WIDTH / 2) - (Game_Map::TILE_WIDTH / 2)) * Game_Map::X_SUBPIXELS)
PSC::Screen.redefine(Game_Player, :SCREEN_CENTER_Y,
                     ((Settings::SCREEN_HEIGHT / 2) - (Game_Map::TILE_HEIGHT / 2)) * Game_Map::Y_SUBPIXELS)

# Map viewports made when Spriteset_Global/Spriteset_Map loaded.
[[Spriteset_Global, [:@@viewport2]],
 [Spriteset_Map, [:@@viewport0, :@@viewport1, :@@viewport3]]].each do |klass, vars|
  vars.each do |var|
    next if !klass.class_variable_defined?(var)
    klass.class_variable_get(var).rect = Rect.new(0, 0, Settings::SCREEN_WIDTH, Settings::SCREEN_HEIGHT)
  end
end

# pbSetResizeFactor runs Graphics.resize_screen once, then sets Graphics.scale.
# mkxp-z applies the resize on the next frame and resets the scale to 1.0, so
# the window would open at 480x320. Set the scale again after that frame.
alias psc_screen_set_resize_factor pbSetResizeFactor
def pbSetResizeFactor(factor)
  first_resize = !$ResizeInitialized
  psc_screen_set_resize_factor(factor)
  return if !first_resize || factor < 0 || factor == 4
  Graphics.update
  Graphics.scale = (factor + 1) * 0.5
  Graphics.center
end

# Lets a plugin give an IconSprite a bitmap it built in code (e.g. a squeezed
# copy). IconSprite#update leaves it alone because no file bitmap is set; the
# sprite disposes it.
class IconSprite
  def psc_replace_bitmap(bitmap)
    clearBitmaps
    @psc_bitmap&.dispose
    @psc_bitmap = bitmap
    self.bitmap = bitmap
  end

  alias psc_screen_dispose dispose
  def dispose
    psc_screen_dispose
    @psc_bitmap&.dispose
    @psc_bitmap = nil
  end
end
