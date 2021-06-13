from app.nanovg import window,vg
from app import tool

from OpenGL import GL
#tool.testrise()
"""
glwin = window.window('图表',640,480)
graph = window.fpsGraph()
def render(_vg,dt,w,h):
    vg.nvgBeginFrame(_vg, w, h, w / h)
    graph.update(dt)
    graph.render(_vg,5,5)
    vg.nvgSave(_vg)
    vg.nvgBeginPath(_vg)
    vg.nvgRoundedRect(_vg, 1,1,w-2,h-2, 10)
    vg.nvgFillColor(_vg, vg.nvgRGBA(28,30,34,192))
    vg.nvgFillColor(_vg, vg.nvgRGBA(0,0,0,128))
    vg.nvgFill(_vg)    
    vg.nvgEndFrame(_vg)
glwin._render = render
glwin.setInterval(10)
glwin.run()
"""