"""nanovg wrapper"""
from ctypes import CDLL, POINTER, Structure, Union,c_int,c_uint,c_void_p,c_float,c_char_p,c_ubyte,c_bool

_path = '/'.join(str.split(__file__,'\\')[:-1])
glew_path = '%s/glew32.dll'%_path
nanovg_path = '%s/nanovg.dll'%_path
glew = CDLL(glew_path)
nanovg = CDLL(nanovg_path)

def _bind(funcname, args=None, returns=None,lib=nanovg):
    func = getattr(lib, funcname, None)
    if not func:
        e = "Could not find function '%s'"
        raise ValueError(e % (funcname))
    func.argtypes = args
    func.restype = returns
    return func
"""
glew.h
"""
GLEW_OK=0
GLEW_NO_ERROR=0
GLEW_ERROR_NO_GL_VERSION=1
GLEW_ERROR_GL_VERSION_10_ONLY=2
#GLEW_ERROR_GLX_VERSION_11_ONLY 3  /* Need at least GLX 1.2 */
glewInit = _bind('glewInit',[],c_int,glew)
glewIsSupported = _bind('glewIsSupported',[c_char_p],c_bool,glew)
glewGetExtension = _bind('glewGetExtension',[c_char_p],c_bool,glew)
glewGetErrorString = _bind('glewGetErrorString',[c_int],POINTER(c_ubyte),glew)
glewGetString = _bind('glewGetString',[c_int],POINTER(c_ubyte),glew)
"""
nanovg_gl.h
"""
NVG_ANTIALIAS 		= 1<<0
NVG_STENCIL_STROKES	= 1<<1
NVG_DEBUG 			= 1<<2

class NVGcontext(c_void_p):
    pass
GLuint = c_uint

nvgCreateGLES = _bind('nvgCreateGLES3',[c_int],POINTER(NVGcontext))
nvgDeleteGLES = _bind('nvgDeleteGLES3',[POINTER(NVGcontext)])
nvglCreateImageFromHandleGLES = _bind('nvglCreateImageFromHandleGLES3',[POINTER(NVGcontext),GLuint,c_int,c_int,c_int],c_int)
nvglImageHandleGLES = _bind('nvglImageHandleGLES3',[POINTER(NVGcontext),c_int],c_uint)

"""
nanovg_gl_utils.h
"""
class NVGLUframebuffer(Structure):
    _fields_ = [
        ('ctx',POINTER(NVGcontext)),
        ('fbo',GLuint),
        ('rbo',GLuint),
        ('texture',GLuint),
        ('image',c_int)
    ]

nvgluBindFramebuffer = _bind('nvgluBindFramebuffer',[POINTER(NVGLUframebuffer)])
nvgluCreateFramebuffer = _bind('nvgluCreateFramebuffer',[POINTER(NVGcontext),c_int,c_int,c_int],POINTER(NVGLUframebuffer))
nvgluDeleteFramebuffer = _bind('nvgluDeleteFramebuffer',[POINTER(NVGLUframebuffer)])

"""
nanovg.h
"""
class _Rgba(Structure):
    _fields_ = [
        ('r',c_float),
        ('g',c_float),
        ('b',c_float),
        ('a',c_float)
    ]    
class NVGcolor(Union):
    _anonymous_ = ("c",)
    _fields_ = [
        ('rgba',(c_float*4)),
        ('c',_Rgba)
    ]

class NVGpaint(Structure):
        _fields_ = [
        ('xform',(c_float*6)),
        ('extent',(c_float*2)),
        ('radius',c_float),
        ('feather',c_float),
        ('innerColor',NVGcolor),
        ('outerColor',NVGcolor),
        ('image',c_int)
    ]

NVG_CCW = 1
NVG_CW = 2
NVG_SOLID = 1
NVG_HOLE = 2

NVG_BUTT=0
NVG_ROUND=1
NVG_SQUARE=2
NVG_BEVEL=3
NVG_MITER=4

NVG_ALIGN_LEFT 		= 1<<0
NVG_ALIGN_CENTER 	= 1<<1
NVG_ALIGN_RIGHT 	= 1<<2
NVG_ALIGN_TOP 		= 1<<3
NVG_ALIGN_MIDDLE	= 1<<4
NVG_ALIGN_BOTTOM	= 1<<5
NVG_ALIGN_BASELINE	= 1<<6

NVG_ZERO = 1<<0
NVG_ONE = 1<<1
NVG_SRC_COLOR = 1<<2
NVG_ONE_MINUS_SRC_COLOR = 1<<3
NVG_DST_COLOR = 1<<4
NVG_ONE_MINUS_DST_COLOR = 1<<5
NVG_SRC_ALPHA = 1<<6
NVG_ONE_MINUS_SRC_ALPHA = 1<<7
NVG_DST_ALPHA = 1<<8
NVG_ONE_MINUS_DST_ALPHA = 1<<9
NVG_SRC_ALPHA_SATURATE = 1<<10

NVG_SOURCE_OVER=0
NVG_SOURCE_IN=1
NVG_SOURCE_OUT=2
NVG_ATOP=3
NVG_DESTINATION_OVER=4
NVG_DESTINATION_IN=5
NVG_DESTINATION_OUT=6
NVG_DESTINATION_ATOP=7
NVG_LIGHTER=8
NVG_COPY=9
NVG_XOR=10

class NVGcompositeOperationState(Structure):
    _fields_=[
        ('srcRGB',c_int),
        ('dstRGB',c_int),
        ('srcAlpha',c_int),
        ('dstAlpha',c_int)
    ]

class NVGglyphPosition(Structure):
    _fields_ = [
        ('str',c_char_p),
        ('x',c_float),
        ('minx',c_int),
        ('maxx',c_int)
    ]

class NVGtextRow(Structure):
    _fields_ = [
        ('start',c_char_p),
        ('end',c_char_p),
        ('next',c_char_p),
        ('width',c_float),
        ('minx',c_float),
        ('maxx',c_float)
    ]

NVG_IMAGE_GENERATE_MIPMAPS	= 1<<0
NVG_IMAGE_REPEATX			= 1<<1
NVG_IMAGE_REPEATY			= 1<<2
NVG_IMAGE_FLIPY				= 1<<3
NVG_IMAGE_PREMULTIPLIED		= 1<<4
NVG_IMAGE_NEAREST			= 1<<5
#Frame
nvgBeginFrame = _bind('nvgBeginFrame',[POINTER(NVGcontext),c_float,c_float,c_float])
nvgCancelFrame = _bind('nvgCancelFrame',[POINTER(NVGcontext)])
nvgEndFrame = _bind('nvgEndFrame',[POINTER(NVGcontext)])
nvgGlobalCompositeOperation = _bind('nvgGlobalCompositeOperation',[POINTER(NVGcontext),c_int])
nvgGlobalCompositeBlendFunc = _bind('nvgGlobalCompositeBlendFunc',[POINTER(NVGcontext),c_int,c_int])
nvgGlobalCompositeBlendFuncSeparate = _bind('nvgGlobalCompositeBlendFuncSeparate',[POINTER(NVGcontext),c_int,c_int,c_int,c_int])
#Color utils
nvgRGB = _bind('nvgRGB',[c_ubyte,c_ubyte,c_ubyte],NVGcolor)
nvgRGBf = _bind('nvgRGBf',[c_float,c_float,c_float],NVGcolor)
nvgRGBA = _bind('nvgRGBA',[c_ubyte,c_ubyte,c_ubyte,c_ubyte],NVGcolor)
nvgRGBAf = _bind('nvgRGBAf',[c_float,c_float,c_float,c_float],NVGcolor)
nvgLerpRGBA = _bind('nvgLerpRGBA',[NVGcolor,NVGcolor,c_float],NVGcolor)
nvgTransRGBA = _bind('nvgTransRGBA',[NVGcolor,c_ubyte],NVGcolor)
nvgTransRGBAf = _bind('nvgTransRGBAf',[NVGcolor,c_float],NVGcolor)
nvgHSL = _bind('nvgHSL',[c_float,c_float,c_float],NVGcolor)
nvgHSLA = _bind('nvgHSLA',[c_float,c_float,c_float,c_ubyte],NVGcolor)
#State Handling
nvgSave = _bind('nvgSave',[POINTER(NVGcontext)])
nvgRestore = _bind('nvgRestore',[POINTER(NVGcontext)])
nvgReset = _bind('nvgReset',[POINTER(NVGcontext)])
#Render styles
nvgShapeAntiAlias = _bind('nvgShapeAntiAlias',[POINTER(NVGcontext),c_int])
nvgStrokeColor = _bind('nvgStrokeColor',[POINTER(NVGcontext),NVGcolor])
nvgStrokePaint = _bind('nvgStrokePaint',[POINTER(NVGcontext),NVGpaint])
nvgFillColor = _bind('nvgFillColor',[POINTER(NVGcontext),NVGcolor])
nvgFillPaint = _bind('nvgFillPaint',[POINTER(NVGcontext),NVGpaint])
nvgMiterLimit = _bind('nvgMiterLimit',[POINTER(NVGcontext),c_float])
nvgStrokeWidth = _bind('nvgStrokeWidth',[POINTER(NVGcontext),c_float])
nvgLineCap = _bind('nvgLineCap',[POINTER(NVGcontext),c_int])
nvgLineJoin = _bind('nvgLineJoin',[POINTER(NVGcontext),c_int])
nvgGlobalAlpha = _bind('nvgGlobalAlpha',[POINTER(NVGcontext),c_float])
#Transforms
nvgResetTransform = _bind('nvgResetTransform',[POINTER(NVGcontext)])
nvgTransform = _bind('nvgTransform',[POINTER(NVGcontext),c_float,c_float,c_float,c_float,c_float,c_float])
nvgTranslate = _bind('nvgTranslate',[POINTER(NVGcontext),c_float,c_float])
nvgRotate = _bind('nvgRotate',[POINTER(NVGcontext),c_float])
nvgSkewX = _bind('nvgSkewX',[POINTER(NVGcontext),c_float])
nvgSkewY = _bind('nvgSkewY',[POINTER(NVGcontext),c_float])
nvgScale = _bind('nvgScale',[POINTER(NVGcontext),c_float,c_float])
nvgCurrentTransform = _bind('nvgCurrentTransform',[POINTER(NVGcontext),POINTER(c_float)])
nvgTransformIdentity = _bind('nvgTransformIdentity',[POINTER(c_float)])
nvgTransformTranslate = _bind('nvgTransformTranslate',[POINTER(c_float),c_float,c_float])
nvgTransformScale = _bind('nvgTransformScale',[POINTER(c_float),c_float,c_float])
nvgTransformRotate = _bind('nvgTransformRotate',[POINTER(c_float),c_float])
nvgTransformSkewX = _bind('nvgTransformSkewX',[POINTER(c_float),c_float])
nvgTransformSkewY = _bind('nvgTransformSkewY',[POINTER(c_float),c_float])
nvgTransformMultiply = _bind('nvgTransformMultiply',[POINTER(c_float),POINTER(c_float)])
nvgTransformPremultiply = _bind('nvgTransformPremultiply',[POINTER(c_float),POINTER(c_float)])
nvgTransformInverse = _bind('nvgTransformInverse',[POINTER(c_float),POINTER(c_float)],c_int)
nvgTransformPoint = _bind('nvgTransformPoint',[POINTER(c_float),POINTER(c_float),POINTER(c_float),c_float,c_float])
nvgDegToRad = _bind('nvgDegToRad',[c_float],c_float)
nvgRadToDeg = _bind('nvgRadToDeg',[c_float],c_float)
#Images
nvgCreateImage = _bind('nvgCreateImage',[POINTER(NVGcontext),c_char_p,c_int],c_int)
nvgCreateImageMem = _bind('nvgCreateImageMem',[POINTER(NVGcontext),c_int,c_char_p,c_int],c_int)
nvgCreateImageRGBA = _bind('nvgCreateImageRGBA',[POINTER(NVGcontext),c_int,c_int,c_int,POINTER(c_ubyte)],c_int)
nvgUpdateImage = _bind('nvgUpdateImage',[POINTER(NVGcontext),c_int,POINTER(c_ubyte)])
nvgImageSize = _bind('nvgImageSize',[POINTER(NVGcontext),c_int,POINTER(c_int),POINTER(c_int)])
nvgDeleteImage = _bind('nvgDeleteImage',[POINTER(NVGcontext),c_int])
#Paints
nvgLinearGradient = _bind('nvgLinearGradient',[POINTER(NVGcontext),c_float,c_float,c_float,c_float,NVGcolor,NVGcolor],NVGpaint)
nvgBoxGradient = _bind('nvgBoxGradient',[POINTER(NVGcontext),c_float,c_float,c_float,c_float,c_float,c_float,NVGcolor,NVGcolor],NVGpaint)
nvgRadialGradient = _bind('nvgRadialGradient',[POINTER(NVGcontext),c_float,c_float,c_float,c_float,NVGcolor,NVGcolor],NVGpaint)
nvgImagePattern = _bind('nvgImagePattern',[POINTER(NVGcontext),c_float,c_float,c_float,c_float,c_float,c_int,c_float],NVGpaint)
#Scissoring
nvgScissor = _bind('nvgScissor',[POINTER(NVGcontext),c_float,c_float,c_float,c_float])
nvgIntersectScissor = _bind('nvgIntersectScissor',[POINTER(NVGcontext),c_float,c_float,c_float,c_float])
nvgResetScissor = _bind('nvgResetScissor',[POINTER(NVGcontext)])
#Paths
nvgBeginPath = _bind('nvgBeginPath',[POINTER(NVGcontext)])
nvgMoveTo = _bind('nvgMoveTo',[POINTER(NVGcontext),c_float,c_float])
nvgLineTo = _bind('nvgLineTo',[POINTER(NVGcontext),c_float,c_float])
nvgLine = _bind('nvgLine',[POINTER(NVGcontext),POINTER(c_float),c_int,POINTER(c_float)])
nvgBezierTo = _bind('nvgBezierTo',[POINTER(NVGcontext),c_float,c_float,c_float,c_float,c_float,c_float])
nvgQuadTo = _bind('nvgQuadTo',[POINTER(NVGcontext),c_float,c_float,c_float,c_float])
nvgArcTo = _bind('nvgArcTo',[POINTER(NVGcontext),c_float,c_float,c_float,c_float,c_float])
nvgClosePath = _bind('nvgClosePath',[POINTER(NVGcontext)])
nvgPathWinding = _bind('nvgPathWinding',[POINTER(NVGcontext),c_int])
nvgRect = _bind('nvgRect',[POINTER(NVGcontext),c_float,c_float,c_float,c_float])
nvgRoundedRect = _bind('nvgRoundedRect',[POINTER(NVGcontext),c_float,c_float,c_float,c_float,c_float])
nvgRoundedRectVarying = _bind('nvgRoundedRectVarying',[POINTER(NVGcontext),c_float,c_float,c_float,c_float,c_float,c_float,c_float,c_float])
nvgEllipse = _bind('nvgEllipse',[POINTER(NVGcontext),c_float,c_float,c_float,c_float])
nvgCircle = _bind('nvgCircle',[POINTER(NVGcontext),c_float,c_float,c_float])
nvgFill = _bind('nvgFill',[POINTER(NVGcontext)])
nvgStroke = _bind('nvgStroke',[POINTER(NVGcontext)])
#Text
nvgCreateFont = _bind('nvgCreateFont',[POINTER(NVGcontext),c_char_p,c_char_p],c_int)
nvgCreateFontAtIndex = _bind('nvgCreateFontAtIndex',[POINTER(NVGcontext),c_char_p,c_char_p,c_int],c_int)
nvgCreateFontMem = _bind('nvgCreateFontMem',[POINTER(NVGcontext),c_char_p,c_char_p,c_int,c_int],c_int)
nvgCreateFontMemAtIndex = _bind('nvgCreateFontMemAtIndex',[POINTER(NVGcontext),c_char_p,c_ubyte,c_int,c_int,c_int],c_int)
nvgFindFont = _bind('nvgFindFont',[POINTER(NVGcontext),c_char_p],c_int)
nvgAddFallbackFontId = _bind('nvgAddFallbackFontId',[POINTER(NVGcontext),c_int,c_int],c_int)
nvgAddFallbackFont = _bind('nvgAddFallbackFont',[POINTER(NVGcontext),c_char_p,c_char_p],c_int)
nvgResetFallbackFontsId = _bind('nvgResetFallbackFontsId',[POINTER(NVGcontext),c_int],c_int)
nvgResetFallbackFonts = _bind('nvgResetFallbackFonts',[POINTER(NVGcontext),c_char_p]) 
nvgFontSize = _bind('nvgFontSize',[POINTER(NVGcontext),c_float]) 
nvgFontBlur = _bind('nvgFontBlur',[POINTER(NVGcontext),c_float]) 
nvgTextLetterSpacing = _bind('nvgTextLetterSpacing',[POINTER(NVGcontext),c_float]) 
nvgTextLineHeight = _bind('nvgTextLineHeight',[POINTER(NVGcontext),c_float]) 
nvgTextAlign = _bind('nvgTextAlign',[POINTER(NVGcontext),c_int])
nvgFontFaceId = _bind('nvgFontFaceId',[POINTER(NVGcontext),c_int])
nvgFontFace = _bind('nvgFontFace',[POINTER(NVGcontext),c_char_p])
nvgText = _bind('nvgText',[POINTER(NVGcontext),c_float,c_float,c_char_p,c_char_p],c_float)
nvgTextBox = _bind('nvgTextBox',[POINTER(NVGcontext),c_float,c_float,c_float,c_char_p,c_char_p])
nvgTextBounds = _bind('nvgTextBounds',[POINTER(NVGcontext),c_float,c_float,c_char_p,c_char_p,POINTER(c_float)],c_float)
nvgTextBoxBounds = _bind('nvgTextBoxBounds',[POINTER(NVGcontext),c_float,c_float,c_float,c_char_p,c_char_p,POINTER(c_float)])
nvgTextGlyphPositions = _bind('nvgTextGlyphPositions',[POINTER(NVGcontext),c_float,c_float,c_char_p,c_char_p,POINTER(NVGglyphPosition),c_int],c_int)
nvgTextMetrics = _bind('nvgTextMetrics',[POINTER(NVGcontext),POINTER(c_float),POINTER(c_float),POINTER(c_float)])
nvgTextBreakLines = _bind('nvgTextBreakLines',[POINTER(NVGcontext),c_char_p,c_char_p,c_float,POINTER(NVGtextRow),c_int],c_int)
#Internal Render API