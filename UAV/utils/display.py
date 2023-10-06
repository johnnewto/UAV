


__all__ = ['show_image', 'puttext', 'ScrollingLog', 'ScrollingLogHandler', 'VideoWriter', 'doc_class']


def _fig_bounds(x):
    r = x//32
    return min(5, max(1,r))


from fastcore.utils import *
import cv2
import numpy as np

import matplotlib.pyplot as plt
import moviepy.editor as mvp
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter
import logging
import UAV.params as params
from nbdev.showdoc import *
import inspect

# logging.getLogger('matplotlib.font_manager').disabled = True   # disable matplotlib font manager warnings
logging.getLogger('matplotlib').setLevel(logging.WARNING) # disable matplotlib font manager debug messages


# Todo Test for ipython  see def in_ipython(): in fastcore  or imports.py
def show_image(im
               , ax=None  # if None, a new figure is created
               , figsize=None # if None, the figure size is set to min of 5 and max of 1/32 of the image size
               , title=None # title of the image
               , text=None # text to be written on image
               , fontsize=12 # fontsize of text
               , ctx=None # context
               , rgb2bgr:bool=False # convert from/to RGB
               , **kwargs # kwargs for matplotlib
    )->plt.Axes: # return matplotlib axis
    "Show a PIL or PyTorch image on `ax`."
    # Handle pytorch axis order
    if hasattrs(im, ('data','cpu','permute')):
        im = im.data.cpu()
        if im.shape[0]<5: im=im.permute(1,2,0)
    elif not isinstance(im,np.ndarray): im=np.ndarray(im)
    # Handle 1-channel images
    if im.shape[-1]==1: im=im[...,0]
    if rgb2bgr:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    ax = ifnone(ax,ctx)
    if figsize is None: figsize = (_fig_bounds(im.shape[0]), _fig_bounds(im.shape[1]))
    if ax is None: fig,ax = plt.subplots(figsize=figsize)
    ax.imshow(im, **kwargs)
    
    if text is not None:
        ymin, ymax = ax.get_ylim()
        xmin, xmax = ax.get_xlim()
        # Compute the height of the image in data units
        image_height = ymax - ymin
        image_width = xmax - xmin
        # Set the position of the text to be 10% of the image height
        text_height = -0.1 * image_height
        text_width = 0.05 * image_width
        xpos = text_width
        ypos = text_height
        ax.text(xpos, ypos, text, fontsize=fontsize, bbox=dict(facecolor='white', edgecolor='none', pad=0)) 
        
    if title is not None: ax.set_title(title)
    ax.axis('off')
    return ax


def puttext(img
            , text:str    # text to be written on image
            , pos=(40,80)  # position of text
            , fontscale=2.0 # fontscale of text
            , thickness=2    # thickness of text
            , textcolor=(255,255,255)   # color of text
            , backcolor=(0,0,0)):   # color of background
    """ Place text on the image, the default position is the center of the image"""
    
    text_width, text_height = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontscale, 1)[0]
    
    if pos is None:
        pos = (img.shape[1]//2-text_width//2, img.shape[0]//2+text_height//2)
    
    rs_point = (pos[0]-2, pos[1]+2)
    re_point = (pos[0]+text_width+4, pos[1]-text_height-2)
    img = cv2.rectangle(img, rs_point, re_point, backcolor, -1)
    return cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, fontscale, textcolor, thickness, cv2.LINE_AA)


class ScrollingLog:
    """Draws a  scrolling log of messages onto an image"""
    def __init__(self, 
                 max_lines:int=5, # max number of lines to display
                 position:Union[tuple,None]=None, # position of the log (x, y) or None
                 color:tuple=(255, 0, 0), # color of the log
                 bg_color:Union[tuple,None]=None, # background color of the log
                 thickness:int=2, # thickness of the log
                 font_scale:float=1.0, # font scale of the log
                 ): 

        self.max_lines = max_lines
        self.color = color
        self.bg_color = bg_color
        self.thickness = thickness
        self.font_scale = font_scale
        self.position = position
        self.log = []
        
    def update(self, message:str,  # add a message to the log
               index=None): # index of the message to be updated
        """Add a message to the log, if index is specified, update the message at the index"""
        if index is not None:
            # Replace message at the specified index
            if 0 <= index < len(self.log):
                self.log[index] = message

            else:
                print(f"Warning:  0 <= index < len(self.log)")
                self.log[-1] = message
        else:
            # Normal scrolling log behavior or index out of range
            self.log.append(message)
            if len(self.log) > self.max_lines:
                self.log.pop(0)
                
    def draw(self, image, font=cv2.FONT_HERSHEY_SIMPLEX):
        """Draw the log on the image"""
        if len(self.log) == 0:
            return
        # Calculate the font size based on the image size
        font_size = (self.font_scale * image.shape[0]) / 1000.0
        (_, line_height), _ = cv2.getTextSize(self.log[0], font, font_size, self.thickness)
        # line_height = int(font_size * 30)
        line_height = int(line_height * 1.5)
        if self.position is None:
            self.position = (line_height, line_height)
        
        # Draw background rectangles first  so no to overwrite the text hanging parts  
        y_offset = 0
        if self.bg_color is not None:
            for message in self.log:
                y = self.position[1] + y_offset
                # Getting the text size to create the background rectangle
                (text_width, text_height), _ = cv2.getTextSize(message, font, font_size, self.thickness)
                rectangle_start = (self.position[0], y - text_height - 5)
                rectangle_end = (self.position[0] + text_width, y+15)
                # Drawing the background rectangle
                cv2.rectangle(image, rectangle_start, rectangle_end, self.bg_color, -1)
                y_offset += line_height

        # draw text on background rectangle
        y_offset = 0
        for message in self.log:
            y = self.position[1] + y_offset
            cv2.putText(image, message, (self.position[0], y), font, font_size, self.color, self.thickness)
            y_offset += line_height




class ScrollingLogHandler(logging.Handler ):
    """Handler for ScrollingLog: Takes logger messages and places them on the scrolling log display"""
    def __init__(self, scrolling_log: ScrollingLog, # ScrollingLog object
                 logger:logging.Logger, # logger object, this ensures that the handler is attached to the logger. 
                 _filter: str = '', # filter for the log message
                 format: str = '%(levelname)s - %(message)s',
                 ): # format of the log message
        super().__init__()
        self.scrolling_log = scrolling_log
        self._filter = _filter
        # Handler for ScrollingLog
        formatter_log = logging.Formatter(format)
        self.setFormatter(formatter_log)
        logger.addHandler(self)
        logger.setLevel(params.LOGGING_LEVEL)   # todo add this to params
        
    def set_filter(self, _filter:str):
        """Set the filter for the log message"""
        self._filter = _filter
        
    def emit(self, record):
        log_entry = self.format(record)
        if len(self._filter) > 0 and self._filter not in log_entry:
            # print(f"Filtering out log entry: {log_entry}")
            return
        self.scrolling_log.update(log_entry)



class VideoWriter:
    """A wrapper around FFMPEG_VideoWriter to write videos from images"""
    def __init__(self, 
                 filename:str='_autoplay.mp4', # default filename
                 fps:float=30.0, #    fps of video
                 rgb2bgr:bool=False, # convert to RGB
                 **kw): # kwargs for FFMPEG_VideoWriter
        self.writer = None
        self.rgb2bgr=rgb2bgr,
        self.params = dict(filename=filename, fps=fps, **kw)
        print(f"Writing video to {Path.cwd()/filename} at {fps} fps.")

    def add(self, 
            img:np.ndarray # image to be added
            )->None:
        """Add an image to the video"""
        img = np.asarray(img)
        if self.writer is None:
            h, w = img.shape[:2]
            self.writer = FFMPEG_VideoWriter(size=(w, h), **self.params)
        if img.dtype in [np.float32, np.float64]:
            img = np.uint8(img.clip(0, 1) * 255)
        if len(img.shape) == 2:
            img = np.repeat(img[..., None], 3, -1)
        if self.rgb2bgr:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.writer.write_frame(img)

    def close(self):
        if self.writer:
            self.writer.close()

    def __enter__(self):
        return self

    def __exit__(self, *kw):
        self.close()
        if self.params['filename'] == '_autoplay.mp4':
            self.show()

    def show(self, **kw):
        """Show the video"""
        self.close()
        fn = self.params['filename']
        print (f"Video: {Path.cwd()/fn}")
        display(mvp.ipython_display(fn, **kw))


class ClassMarkdownRenderer():
    """Markdown renderer for a class. Renders all the public methods in one go in a Jupyter notebook."""

    def __init__(self, doclist):
        self.doclist = doclist

    def _repr_markdown_(self):
        """ Markdown representation for Jupyter notebooks."""
        docstr = ''
        for doc in self.doclist:
            docstr += doc
            docstr += '\n\n'
        return docstr

    __repr__ = __str__ = _repr_markdown_


def doc_class(cls):
    """ Document all the public methods in a class"""

    # for name, obj in inspect.getmembers(cls, inspect.iscoroutinefunction):
    #     obj.__name__ = 'async ' + obj.__name__    # note that this is not a coroutine function
    docs = []
    for name, obj in inspect.getmembers(cls, inspect.isfunction):
        if not name.startswith('_'):
            docs.append(show_doc(obj).__repr__())
            # docs.append(DocmentTbl(obj).__str__())
            if inspect.iscoroutinefunction(obj) :
                docs.append('**Note: async function** ')
                docs.append(DocmentTbl(obj).__str__())

    # docs = [show_doc(obj).__repr__() for name, obj in inspect.getmembers(cls, inspect.isfunction) if
    #         not (name.startswith('_'))]
    return ClassMarkdownRenderer(docs)