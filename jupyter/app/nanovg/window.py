import ctypes
from ctypes import c_int
from OpenGL import GL
import sdl2
from sdl2 import video
from sdl2.timer import SDL_GetTicks
from . import vg

"""
定义一个基本的VG窗口类
"""
class window:
    def __init__(self,title,w,h):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            raise RuntimeError('SDL_Init')

        self._window = sdl2.SDL_CreateWindow(title.encode('utf-8'),
                                    sdl2.SDL_WINDOWPOS_UNDEFINED,
                                    sdl2.SDL_WINDOWPOS_UNDEFINED, w, h,
                                    sdl2.SDL_WINDOW_OPENGL|sdl2.SDL_WINDOW_RESIZABLE)
        if not window:
            raise RuntimeError('SDL_CreateWindow')
        self._context = sdl2.SDL_GL_CreateContext(self._window)
        sdl2.SDL_GL_MakeCurrent(self._window,self._context)
        if vg.glewInit()!=vg.GLEW_OK:
            raise RuntimeError('glewInit')
        self._vg = vg.nvgCreateGLES(vg.NVG_ANTIALIAS | vg.NVG_STENCIL_STROKES)
        if not self._vg:
            raise RuntimeError('nvgCreateGLES')
        self._render  = None
        self._running = True
        self._fps = 0
        self._interval = -1
        sdl2.SDL_GL_SetSwapInterval(0)

    def run(self):
        event = sdl2.SDL_Event()
        prevt = 0
        acc = 0
        while self._running:
            while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == sdl2.SDL_QUIT:
                    self._running = False
            t = SDL_GetTicks()/1000.
            dt = t-prevt
            prevt = t
            if self._interval>0 and acc>self._interval:
                acc = 0
                self.update(dt)
            acc+=dt
            sdl2.SDL_Delay(10)

    def setInterval(self,r):
        self._fps = r
        if r>0:
            self._interval = 1./r
        else:
            self._interval = -1

    def update(self,dt):
        w,h = c_int(),c_int()
        video.SDL_GetWindowSize(self._window, ctypes.byref(w), ctypes.byref(h))
        fbWidth,fbHeight = w.value,h.value
        GL.glViewport(0, 0, fbWidth, fbHeight)
        if False:
            GL.glClearColor(0, 0, 0, 0)
        else:
            GL.glClearColor(0.3, 0.3, 0.32, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT | GL.GL_STENCIL_BUFFER_BIT)
        
        if self._render is not None:
            self._render(self._vg,dt,fbWidth,fbHeight)
        
        sdl2.SDL_GL_SwapWindow(self._window)

class fpsGraph:
    def __init__(self):
        self._values = [0]*100
        self._head = 0
    def update(self,frameTime):
        self._head = (self._head+1)%100
        self._values[self._head] = frameTime
    def getGraphAverage(self):
        avg = 0
        for i in range(100):
            avg += self._values[i]
        return avg/100.
    def render(self,_vg,x,y):
        avg = self.getGraphAverage()
        w = 200
        h = 35
        vg.nvgBeginPath(_vg)
        vg.nvgRect(_vg, x,y, w,h)
        vg.nvgFillColor(_vg, vg.nvgRGBA(0,0,0,128))
        vg.nvgFill(_vg)
        vg.nvgBeginPath(_vg)
        vg.nvgMoveTo(_vg, x, y+h)

        for i in range(100):
            v = 1.0 / (0.00001 + self._values[(self._head+i) % 100])
            if v > 80.0:
                v = 80.0
            vx = x + (float(i)/(100-1)) * w
            vy = y + h - ((v / 80.0) * h)
            vg.nvgLineTo(_vg, vx, vy)
        
        vg.nvgLineTo(_vg, x+w, y+h)
        vg.nvgFillColor(_vg, vg.nvgRGBA(255,192,0,128))
        vg.nvgFill(_vg)

        vg.nvgFontFace(_vg, b"sans")

        vg.nvgFontSize(_vg, 15.0)
        vg.nvgTextAlign(_vg,vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_TOP)
        vg.nvgFillColor(_vg, vg.nvgRGBA(240,240,240,255))
        s = b"%.2f FPS"%(1.0 / avg)
        vg.nvgText(_vg, x+w-3,y+3, s, None)
        vg.nvgFontSize(_vg, 13.)
        vg.nvgTextAlign(_vg,vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_BASELINE)
        vg.nvgFillColor(_vg, vg.nvgRGBA(240,240,240,160))
        s = b"%.2f ms"%(avg * 1000.0)
        vg.nvgText(_vg, x+w-3,y+h-3, s, None)
