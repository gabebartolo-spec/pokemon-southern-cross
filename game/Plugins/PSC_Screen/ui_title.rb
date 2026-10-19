#===============================================================================
# Splash and title screens at 480x320. Their images are 512x384.
# - Splashes (centred text): centred, cropping 16 pixels each side and 32 top
#   and bottom.
# - Title: the logo sits at the top of the image, so it is top-aligned and the
#   bottom 64 pixels (the "Version" line) are cropped; the flashing
#   "Press Enter" strip moves into the black band that remains at the bottom.
#===============================================================================
class IntroEventScene
  IMAGE_X       = -PSC::Screen::WIDTH_LOST / 2
  SPLASH_Y      = -PSC::Screen::HEIGHT_LOST / 2
  TITLE_Y       = 0
  START_STRIP_FROM_BOTTOM = 20
  PSC::Screen.redefine(self, :TITLE_START_IMAGE_X, TITLE_START_IMAGE_X + IMAGE_X)
  PSC::Screen.redefine(self, :TITLE_START_IMAGE_Y, Settings::SCREEN_HEIGHT - START_STRIP_FROM_BOTTOM)

  alias psc_screen_initialize initialize
  def initialize(viewport = nil)
    psc_screen_initialize(viewport)
    @pic.setXY(0, IMAGE_X, SPLASH_Y)
  end

  alias psc_screen_open_title_screen open_title_screen
  def open_title_screen(scene, *args)
    @pic.setXY(0, IMAGE_X, TITLE_Y)
    psc_screen_open_title_screen(scene, *args)
  end

  # Essentials pauses for a second with @pic.moveXY(0, 20, 0, 0), which would
  # slide the image to 0,0. Pause where the image already is instead.
  alias psc_screen_fade_out_title_screen fade_out_title_screen
  def fade_out_title_screen(scene)
    pic = @pic
    def pic.moveXY(delay, duration, _x, _y, cb = nil)
      super(delay, duration, IntroEventScene::IMAGE_X, IntroEventScene::TITLE_Y, cb)
    end
    psc_screen_fade_out_title_screen(scene)
  end
end
