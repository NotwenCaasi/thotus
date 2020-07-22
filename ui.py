from __future__ import print_function

import sys
import numpy as np
# import skimage.transform
import cv2
from thotus import settings

import asyncio

def imresize(img, size):
    return cv2.resize(img, dsize=size)
#     return skimage.transform.resize(img, size, order=3)

async def resolve(val):
    return val

class GUI:

    name = 'Thot display'

    def __init__(self):
        cv2.namedWindow(self.name)
        self.secondary = []

    def progress(self, text, val, total=100):
        print("\r%s [%d] @ %3d%%"%(text, val, int(100.0*val/total)), end='')
        sys.stdout.flush()

    def clear(self):
        names = [self.name] + self.secondary
        cv2.waitKey(100)
        self.secondary.clear()
        cv2.destroyAllWindows()

    def redraw(self):
        cv2.waitKey(1)

    def ok_cancel(self, duration=10, default=True):
        for n in range(duration):
            x = cv2.waitKey(1000)&0xff
            if x in (27, 8): # backspace or escape
                return False
            elif x in (10, 32): # enter or space
                return True
        return default

    async def display(self, img, text, resize=False, crop=False, disp_number=0):
        print('E-10')###
        image = await resolve(img)###
        if resize:
            print('E-11')###
            if resize == True:
                print('E-12')###
                resize = settings.UI_RATIO
            if isinstance(resize, float):
                print('E-13')###
                #shape = await resolve(image.shape)###
                print(image.shape)###
                #resize = tuple(reversed([int(x*resize) for x in image.shape[:2]]))###
                resize = tuple(reversed([int(x*resize) for x in shape[:2]]))###

        if text:
            print('E-14')###
            black = (0, 0, 0)
            white = (255, 255, 255)
            cv2.putText(image, text, (9, 99), cv2.FONT_HERSHEY_SIMPLEX, 2.0, black)
            cv2.putText(image, text, (12, 102), cv2.FONT_HERSHEY_SIMPLEX, 2.0, black)
            cv2.putText(image, text, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 2.0, white)
            cv2.putText(image, text, (11, 101), cv2.FONT_HERSHEY_SIMPLEX, 2.0, white)

        if resize:
            print('E-15')###
            image = imresize(image, resize)

        if disp_number:
            print('E-16')###
            name = "%s %d"%(self.name, disp_number)
            cv2.imshow(name, image)
            if not name in self.secondary:
                self.secondary.append(name)
        else:
            print('E-17')###
            cv2.imshow(self.name, image)
        print('E-18')###
        self.redraw()
        print('E-19')###

gui = GUI()
