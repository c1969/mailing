import os
from PIL import Image

WIDTH = 1180
HEIGHT = 472
DPI  = 300

class Imager():

    def __init__(self) -> None:
        pass

    def genImage(self, infile):
        im = Image.open(infile)
        return im


    def getOrientation(self, x, y):
        ratio = x / y
        if ratio >= 2.5:
            return 0
        else:
            return 1


    def harmonize(self, img, x, y, orient, filename):
        if orient == 0: #landscape
            p = os.path.join('static', 'upload', filename)
            height_factor = WIDTH / x
            height = int(y * height_factor)
            imr = img.resize((WIDTH, height), Image.NEAREST).convert('RGBA')
            imr.convert('L').save(p+'/'+filename+".png")
            fill_color = (255,255,255)
            background = Image.new(imr.mode[:-1], imr.size, fill_color)
            background.paste(imr, imr.split()[-1])
            background.convert('L').save(p+'/'+filename+".pdf", save_all=True, dpi=(DPI, DPI))
            return 0
        if orient == 1: #portrait
            p = os.path.join('static', 'upload', filename)
            width_factor = HEIGHT / y
            width = int(x * width_factor)
            imr = img.resize((width, HEIGHT), Image.NEAREST).convert('RGBA')
            imr.convert('L').save(p+'/'+filename+".png")
            fill_color = (255,255,255)
            background = Image.new(imr.mode[:-1], imr.size, fill_color)
            background.paste(imr, imr.split()[-1])
            background.convert('L').save(p+'/'+filename+".pdf", save_all=True, dpi=(DPI, DPI))
            return 0