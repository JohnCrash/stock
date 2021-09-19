from . import vg
from ctypes import POINTER,c_float,c_char_p,c_int,byref

class Canvas2d:
    """
    和vg函数一一对应，去掉了nvg前缀。主要用于隐藏ctx上下文，同时对函数参数加上类型
    另外颜色，变换，角度转换这些和上下文没关系的函数不在其中
    """
    def __init__(self,p:int=vg.NVG_ANTIALIAS | vg.NVG_STENCIL_STROKES):
        self._ctx = vg.nvgCreateGLES(p)
        if not self._ctx:
            raise RuntimeError('nvgCreateGLES')
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def createFramebuffer(self,width:int,height:int,imageFlags:int):
        return vg.nvgluCreateFramebuffer(self._ctx,width,height,imageFlags)
    def bindFramebuffer(self,fbo):
        vg.nvgluBindFramebuffer(fbo)
    def deleteFramebuffer(self,fbo):
        vg.nvgluDeleteFramebuffer(fbo)
    def beginFrame(self,windowWidth:float, windowHeight:float, devicePixelRatio:float = 1):
        """
        Begin drawing a new frame
        Calls to nanovg drawing API should be wrapped in nvgBeginFrame() & nvgEndFrame()
        nvgBeginFrame() defines the size of the window to render to in relation currently
        set viewport (i.e. glViewport on GL backends). Device pixel ration allows to
        control the rendering on Hi-DPI devices.
        For example, GLFW returns two dimension for an opened window: window size and
        frame buffer size. In that case you would set windowWidth/Height to the window size
        devicePixelRatio to: frameBufferWidth / windowWidth.        
        """
        vg.nvgBeginFrame(self._ctx,windowWidth,windowHeight,devicePixelRatio)
    def cancelFrame(self):
        """
        Cancels drawing the current frame.
        """
        vg.nvgCancelFrame(self._ctx)
    def endFrame(self):
        """
        Ends drawing flushing remaining render state.
        """
        vg.nvgEndFrame(self._ctx)
    def save(self):
        """
        State Handling
        NanoVG contains state which represents how paths will be rendered.
        The state contains transform, fill and stroke styles, text and font styles,
        and scissor clipping.
        Pushes and saves the current render state into a state stack.
        A matching nvgRestore() must be used to restore the state.        
        """
        vg.nvgSave(self._ctx)
    def restore(self):
        """
        Pops and restores current render state.
        """
        vg.nvgRestore(self._ctx)
    def reset(self):
        """
        Resets current render state to default values. Does not affect the render state stack.                
        """
        vg.nvgReset(self._ctx)
    def shapeAntiAlias(self, enabled:int):
        """
        Sets whether to draw antialias for nvgStroke() and nvgFill(). It's enabled by default.
        """
        vg.nvgShapeAntiAlias(self._ctx,enabled)
    def strokeColor(self,color:vg.NVGcolor):
        """
        Sets current stroke style to a solid color.
        """
        vg.nvgStrokeColor(self._ctx,color)
    def strokePaint(self, paint:vg.NVGpaint):
        """
        Sets current stroke style to a paint, which can be a one of the gradients or a pattern.
        """
        vg.nvgStrokePaint(self._ctx,paint)
    def fillColor(self,color:vg.NVGcolor):
        """
        Sets current fill style to a solid color.
        """
        vg.nvgFillColor(self._ctx,color)
    def fillPaint(self,paint:vg.NVGpaint):
        """
        Sets current fill style to a paint, which can be a one of the gradients or a pattern.
        """
        vg.nvgFillPaint(self._ctx,paint)
    def miterLimit(self,limit:float):
        """
        Sets the miter limit of the stroke style.
        Miter limit controls when a sharp corner is beveled.
        """
        vg.nvgMiterLimit(self._ctx,limit)
    def strokeWidth(self, size:float):
        """
        Sets the stroke width of the stroke style.
        """
        vg.nvgStrokeWidth(self._ctx,size)
    def lineCap(self,cap:int):
        """
        Sets how the end of the line (cap) is drawn,
        Can be one of: NVG_BUTT (default), NVG_ROUND, NVG_SQUARE.        
        """
        vg.nvgLineCap(self._ctx,cap)
    def lineJoin(self,join:int):
        """
        Sets how sharp path corners are drawn.
        Can be one of NVG_MITER (default), NVG_ROUND, NVG_BEVEL.        
        """        
        vg.nvgLineJoin(self._ctx,join)
    def globalAlpha(self,alpha:float):
        """
        Sets the transparency applied to all rendered shapes.
        Already transparent paths will get proportionally more transparent as well.        
        """
        vg.nvgGlobalAlpha(self._ctx,alpha)     
    def resetTransform(self):
        """
        Resets current transform to a identity matrix.
        """
        vg.nvgResetTransform(self._ctx)
    def transform(self,a:float,b:float,c:float,d:float,e:float,f:float):
        """
        Premultiplies current coordinate system by specified matrix.
        The parameters are interpreted as matrix as follows:
          [a c e]
          [b d f]
          [0 0 1]        
        """
        vg.nvgTransform(self._ctx,a,b,c,d,e,f)
    def translate(self,x:float,y:float):
        """
        Translates current coordinate system.
        """
        vg.nvgTranslate(self._ctx, x, y)
    def rotate(self,angle:float):
        """
        Rotates current coordinate system. Angle is specified in radians.
        """
        vg.nvgRotate(self._ctx,angle)
    def skewX(self,angle:float):
        """
        Skews the current coordinate system along X axis. Angle is specified in radians.
        """
        vg.nvgSkewX(self._ctx,angle)
    def skewY(self,angle:float):
        """
        Skews the current coordinate system along Y axis. Angle is specified in radians.
        """
        vg.nvgSkewY(self._ctx,angle)
    def scale(self,x:float,y:float):
        """
        Scales the current coordinate system.
        """        
        vg.nvgScale(self._ctx,x,y)
    def currentTransform(self,xform):
        """
        Stores the top part (a-f) of the current transformation matrix in to the specified buffer.
          [a c e]
          [b d f]
          [0 0 1]
        There should be space for 6 floats in the return buffer for the values a-f.        
        """
        vg.nvgCurrentTransform(self._ctx,xform)
    def createImage(self, filename:str,  imageFlags:int):
        """
        Creates image by loading it from the disk from specified file name.
        Returns handle to the image.
        """
        return vg.nvgCreateImage(self._ctx, filename.encode('utf-8'), imageFlags)
    def createImageMem(self, imageFlags:int, data:c_char_p, ndata:int):
        """
        Creates image by loading it from the specified chunk of memory.
        Returns handle to the image.
        """
        return vg.nvgCreateImageMem(self._ctx, imageFlags, data,ndata)
    def createImageRGBA(self, w:int, h:int, imageFlags:int, data:c_char_p):
        """
        Creates image from specified image data.
        Returns handle to the image.
        """
        return vg.nvgCreateImageRGBA(self._ctx, w, h, imageFlags, data)
    def updateImage(self, image:int, data:c_char_p):
        """
        Updates image data specified by image handle.
        """
        vg.nvgUpdateImage(self._ctx, image, data)
    def imageSize(self, image:int):
        """
        Returns the dimensions of a created image.
        """
        w = c_int()
        h = c_int()
        vg.nvgImageSize(self._ctx, image, byref(w), byref(h))
        return w.value,h.value
    def deleteImage(self, image:int):
        """
        Deletes created image.
        """
        vg.nvgDeleteImage(self._ctx,image)
    def linearGradient(self,sx:float,sy:float,ex:float,ey:float,icol:vg.NVGcolor,ocol:vg.NVGcolor):
        """
        Creates and returns a linear gradient. Parameters (sx,sy)-(ex,ey) specify the start and end coordinates
        of the linear gradient, icol specifies the start color and ocol the end color.
        The gradient is transformed by the current transform when it is passed to nvgFillPaint() or nvgStrokePaint().        
        """
        return vg.nvgLinearGradient(self._ctx, sx, sy, ex, ey,icol,ocol)
    def boxGradient(self,x:float, y:float, w:float, h:float,r:float,f:float, icol:vg.NVGcolor,ocol:vg.NVGcolor):
        """
        Creates and returns a box gradient. Box gradient is a feathered rounded rectangle, it is useful for rendering
        drop shadows or highlights for boxes. Parameters (x,y) define the top-left corner of the rectangle,
        (w,h) define the size of the rectangle, r defines the corner radius, and f feather. Feather defines how blurry
        the border of the rectangle is. Parameter icol specifies the inner color and ocol the outer color of the gradient.
        The gradient is transformed by the current transform when it is passed to nvgFillPaint() or nvgStrokePaint().
        """
        return vg.nvgBoxGradient(self._ctx,x,y,w,h,r,f,icol,ocol)
    def radialGradient(self,cx:float,cy:float, inr:float,outr: float,icol:vg.NVGcolor,ocol:vg.NVGcolor):
        """
        Creates and returns a radial gradient. Parameters (cx,cy) specify the center, inr and outr specify
        the inner and outer radius of the gradient, icol specifies the start color and ocol the end color.
        The gradient is transformed by the current transform when it is passed to nvgFillPaint() or nvgStrokePaint().
        """
        return vg.nvgRadialGradient(self._ctx, cx, cy, inr, outr,icol, ocol)
    def imagePattern(self, ox:float, oy:float, ex:float, ey:float, angle:float,image:int, alpha:float):
        """
        Creates and returns an image pattern. Parameters (ox,oy) specify the left-top location of the image pattern,
        (ex,ey) the size of one image, angle rotation around the top-left corner, image is handle to the image to render.
        The gradient is transformed by the current transform when it is passed to nvgFillPaint() or nvgStrokePaint().
        """
        return vg.nvgImagePattern(self._ctx, ox,oy,ex, ey,angle,image,alpha)
    def scissor(self,x:float , y:float, w:float, h:float):
        """
        Sets the current scissor rectangle.
        The scissor rectangle is transformed by the current transform.
        """
        vg.nvgScissor(self._ctx, x, y, w, h)
    def intersectScissor(self, x:float , y:float , w:float , h:float ):
        """
        Intersects current scissor rectangle with the specified rectangle.
        The scissor rectangle is transformed by the current transform.
        Note: in case the rotation of previous scissor rect differs from
        the current one, the intersection will be done between the specified
        rectangle and the previous scissor rectangle transformed in the current
        transform space. The resulting shape is always rectangle.
        """
        vg.nvgIntersectScissor(self._ctx, x, y, w, h)
    def resetScissor(self):
        """
        Reset and disables scissoring.
        """
        vg.nvgResetScissor(self._ctx)
    def beginPath(self):
        """
        Clears the current path and sub-paths.
        """
        vg.nvgBeginPath(self._ctx)
    def moveTo(self,x:float , y:float ):
        """
        Starts new sub-path with specified point as first point.
        """
        vg.nvgMoveTo(self._ctx,x,y)
    def lineTo(self, x:float , y:float ):
        """
        Adds line segment from the last point in the path to the specified point.
        """
        vg.nvgLineTo(self._ctx, x, y)
    def line(self,pt:POINTER(c_float),n:int,linestyle:tuple=None):
        """
        pt [(x,y),...] 可以使用numpy类型转换ctypes.data_as(c_float_p)
        linestyle = (dw0,dw1,dw2) 点，空，点
        """
        ls =  (0,0,0) if linestyle is None else linestyle
        vg.nvgLine(self._ctx, pt,n,(c_float*3)(*ls))
    def bezierTo(self, c1x:float , c1y:float , c2x:float , c2y:float , x:float , y:float ):
        """
        Adds cubic bezier segment from last point in the path via two control points to the specified point.
        """
        vg.nvgBezierTo(self._ctx, c1x, c1y, c2x, c2y, x, y)
    def quadTo(self, cx:float , cy:float , x:float , y:float ):
        """
        Adds quadratic bezier segment from last point in the path via a control point to the specified point.
        """
        vg.nvgQuadTo(self._ctx, cx, cy, x, y)
    def arcTo(self, x1:float , y1:float , x2:float , y2:float , radius:float ):
        """
        Adds an arc segment at the corner defined by the last path point, and two specified points.
        """
        vg.nvgArcTo(self._ctx, x1, y1, x2, y2, radius)
    def closePath(self):
        """
        Closes current sub-path with a line segment.
        """
        vg.nvgClosePath(self._ctx)
    def pathWinding(self, dir:int ):
        """
        Sets the current sub-path winding, see NVGwinding and NVGsolidity.
        """
        vg.nvgPathWinding(self._ctx, dir)
    def arc(self, cx:float , cy:float , r:float , a0:float , a1:float , dir:int ):
        """
        Creates new circle arc shaped sub-path. The arc center is at cx,cy, the arc radius is r,
        and the arc is drawn from angle a0 to a1, and swept in direction dir (NVG_CCW, or NVG_CW).
        Angles are specified in radians.
        """
        vg.nvgArc(self._ctx, cx, cy, r, a0, a1, dir)
    def rect(self, x:float , y:float , w:float , h:float ):
        """
        Creates new rectangle shaped sub-path.
        """
        vg.nvgRect(self._ctx, x, y, w, h)
    def roundedRect(self, x:float , y:float , w:float , h:float , r:float ):
        """
        Creates new rounded rectangle shaped sub-path.
        """
        vg.nvgRoundedRect(self._ctx, x, y, w, h, r)
    def roundedRectVarying(self, x:float , y:float , w:float , h:float , radTopLeft:float , radTopRight:float , radBottomRight:float , radBottomLeft:float ):
        """
        Creates new rounded rectangle shaped sub-path with varying radii for each corner.
        """
        vg.nvgRoundedRectVarying(self._ctx, x, y, w, h, radTopLeft, radTopRight, radBottomRight, radBottomLeft)
    def ellipse(self, cx:float , cy:float , rx:float , ry:float ):
        """
        Creates new ellipse shaped sub-path.
        """
        vg.nvgEllipse(self._ctx, cx, cy, rx, ry)
    def circle(self, cx:float , cy:float , r:float ):
        """
        Creates new circle shaped sub-path.
        """
        vg.nvgCircle(self._ctx, cx, cy, r)
    def fill(self):
        """
        Fills the current path with current fill style.
        """
        vg.nvgFill(self._ctx)
    def stroke(self):
        """
        Fills the current path with current stroke style.
        """
        vg.nvgStroke(self._ctx)
    def createFont(self, name:str, filename:str):
        """
        Creates font by loading it from the disk from specified file name.
        Returns handle to the font.
        """
        return  vg.nvgCreateFont(self._ctx, name.encode('utf-8'), filename.encode('utf-8'))
    def createFontAtIndex(self, name:str, filename:str, fontIndex:int):
        """
        fontIndex specifies which font face to load from a .ttf/.ttc file.
        """
        return vg.nvgCreateFontAtIndex(self._ctx, name.encode('utf-8'), filename.encode('utf-8'), fontIndex)

    def createFontMem(self, name:str, data:c_char_p, ndata:int, freeData:int):
        """
        Creates font by loading it from the specified memory chunk.
        Returns handle to the font.
        """
        return vg.nvgCreateFontMem(self._ctx, name.encode('utf-8'), data, ndata, freeData)
    def createFontMemAtIndex(self, name:str, data:c_char_p, ndata:int , freeData:int , fontIndex:int):
        """
        fontIndex specifies which font face to load from a .ttf/.ttc file.
        """
        return vg.nvgCreateFontMemAtIndex(self._ctx, name.endcode('utf-8'), data, ndata, freeData, fontIndex)
    def findFont(self, name:str):
        """
        Finds a loaded font of specified name, and returns handle to it, or -1 if the font is not found.
        """
        return vg.nvgFindFont(self._ctx, name.encode('utf-8'))
    def addFallbackFontId(self, baseFont:int , fallbackFont:int ):
        """
        Adds a fallback font by handle.
        """
        return vg.nvgAddFallbackFontId(self._ctx, baseFont, fallbackFont)
    def addFallbackFont(self, baseFont:str, fallbackFont:str):
        """
        Adds a fallback font by name.
        """
        return vg.nvgAddFallbackFont(self._ctx, baseFont.encode('utf-8'), fallbackFont.encode('utf-8'))
    def resetFallbackFontsId(self, baseFont:int ):
        """
        Resets fallback fonts by handle.
        """
        vg.nvgResetFallbackFontsId(self._ctx,baseFont)
    def resetFallbackFonts(self, baseFont:str):
        """
        Resets fallback fonts by name.
        """
        vg.nvgResetFallbackFonts(self._ctx, baseFont.encode('utf-8'))
    def fontSize(self, size:float):
        """
        Sets the font size of current text style.
        """
        vg.nvgFontSize(self._ctx, size)
    def fontBlur(self, blur:float):
        """
        Sets the blur of current text style.
        """
        vg.nvgFontBlur(self._ctx, blur)
    def textLetterSpacing(self, spacing:float ):
        """
        Sets the letter spacing of current text style.
        """
        vg.nvgTextLetterSpacing(self._ctx, spacing)
    def textLineHeight(self, lineHeight:float):
        """
        Sets the proportional line height of current text style. The line height is specified as multiple of font size.
        """
        vg.nvgTextLineHeight(self._ctx, lineHeight)
    def textAlign(self, align:int ):
        """
        Sets the text align of current text style, see NVGalign for options.
        """
        vg.nvgTextAlign(self._ctx, align)
    def fontFaceId(self, font:int):
        """
        Sets the font face based on specified id of current text style.
        """
        vg.nvgFontFaceId(self._ctx, font)
    def fontFace(self, font:str):
        """
        Sets the font face based on specified name of current text style.
        """
        vg.nvgFontFace(self._ctx, font.encode('utf-8'))
    def text(self, x:float , y:float , string:str): #Fixme: 长字符串通过指针取片段
        """
        Draws text string at specified location. If end is specified only the sub-string up to the end is drawn.
        """
        return vg.nvgText(self._ctx, x, y, string.encode('utf-8'), None)
    def textBox(self, x:float , y:float, breakRowWidth:float, string:str): #Fixme 同上
        """
        Draws multi-line text string at specified location wrapped at the specified width. If end is specified only the sub-string up to the end is drawn.
        White space is stripped at the beginning of the rows, the text is split at word boundaries or when new-line characters are encountered.
        Words longer than the max width are slit at nearest character (i.e. no hyphenation).
        """
        return vg.nvgTextBox(self._ctx, x, y, breakRowWidth, string.encode('utf-8'), None)
    def textBounds(self, x:float , y:float, string:str, bounds:POINTER(c_float)): #Fixme 同上
        """
        Measures the specified text string. Parameter bounds should be a pointer to float[4],
        if the bounding box of the text should be returned. The bounds value are [xmin,ymin, xmax,ymax]
        Returns the horizontal advance of the measured text (i.e. where the next character should drawn).
        Measured values are returned in local coordinate space.
        """
        return vg.nvgTextBounds(self._ctx, x, y, string.encode('utf-8'), None, bounds)
    def textBoxBounds(self, x:float, y:float , breakRowWidth:float , string:str, bounds:POINTER(c_float)): #Fixme 同上
        """
        Measures the specified multi-text string. Parameter bounds should be a pointer to float[4],
        if the bounding box of the text should be returned. The bounds value are [xmin,ymin, xmax,ymax]
        Measured values are returned in local coordinate space.
        """
        return vg.nvgTextBoxBounds(self._ctx, x, y, breakRowWidth, string, None, bounds)
    def textGlyphPositions(self, x:float , y:float , string:str, positions:POINTER(vg.NVGglyphPosition), maxPositions:int):
        """
        Calculates the glyph x positions of the specified text. If end is specified only the sub-string will be used.
        Measured values are returned in local coordinate space.
        """
        return vg.nvgTextGlyphPositions(self._ctx, x, y, string.encode('utf-8'), None, positions, maxPositions)
    def textMetrics(self, ascender:POINTER(c_float), descender:POINTER(c_float), lineh:POINTER(c_float)):
        """
        Returns the vertical metrics based on the current text style.
        Measured values are returned in local coordinate space.
        """
        vg.nvgTextMetrics(self._ctx, ascender, descender, lineh)
    def textBreakLines(self, string:str, breakRowWidth:float, rows:POINTER(vg.NVGtextRow), maxRows:int):
        """
        Breaks the specified text into lines. If end is specified only the sub-string will be used.
        White space is stripped at the beginning of the rows, the text is split at word boundaries or when new-line characters are encountered.
        Words longer than the max width are slit at nearest character (i.e. no hyphenation).
        """
        return vg.gTextBreakLines(self._ctx, string.encode('utf-8'), breakRowWidth, rows, maxRows)
