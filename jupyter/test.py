import sys
import os
import sdl2.ext
from sdl2 import video

from app.nanovg import nv

color = nv.nvgRGB(255,128,64)
print(color.rgba[0],color.rgba[1],color.rgba[2])
print(color.r)
print(color.g)
print(color.b)
print(color.a)

RESOURCES = sdl2.ext.Resources(__file__, "images")

sdl2.ext.init()

window = sdl2.ext.Window("Hello World!", size=(1024, 768))
window.show()

factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
sprite = factory.from_image(RESOURCES.get_path("xueqiu.png"))

spriterenderer = factory.create_sprite_render_system(window)
spriterenderer.render(sprite)
# will cause the renderer to draw the sprite 10px to the right and
# 20 px to the bottom
sprite.position = 10, 20

# will cause the renderer to draw the sprite 55px to the right and
# 10 px to the bottom
sprite.position = 55, 10

processor = sdl2.ext.TestEventProcessor()
processor.run(window)