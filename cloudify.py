import importlib
from collections import defaultdict

from thotus.ui import gui
from thotus.image import tools as imtools
from thotus import settings

import cv2
import numpy as np

DEBUG = True

class AnalyseError(Exception): pass

class LineMaker:
    points = None

    registered_algos = {}

    def __getattr__(self, name):
        if name.startswith('from_'):
            realname = name[5:]
            if realname not in self.registered_algos:
                mod = importlib.import_module('thotus.algorithms.algo_%s'%realname)
                setattr(self, name, mod.compute)
            return getattr(self, name)
        raise


def cloudify(*a, **k):
    _ = None
    for _ in iter_cloudify(*a, **k):
        pass
    return _

def iter_cloudify(calibration_data, folder, lasers, sequence, method=None, camera=False, interactive=False, undistort=False):
    print('H-10')###
    pure_images = settings.pure_mode
    lm = LineMaker()
    lineprocessor = getattr(lm, 'from_'+method)
    lm.calibration_data = calibration_data

    print('H-11')###
    sliced_lines = defaultdict(lambda: [None, None])
    color_slices =  defaultdict(lambda: [None, None])

    d_kern = np.ones((3,3),np.uint8)

    RED = 2 # position of red layer

    print('H-12')###
    for i, n in enumerate(sequence):
        print('H-10')###
        yield

        print(folder+'/color_%03d.%s'%(n, settings.FILEFORMAT))

        fullcolor = imtools.imread(folder+'/color_%03d.%s'%(n, settings.FILEFORMAT), format="rgb", calibrated=undistort and calibration_data)
        if fullcolor is None:
            continue

        print('H-13')###
        if pure_images:
            ref_grey = None
        else:
            ref_grey = fullcolor[:,:,RED]

        pictures_todisplay = []

        print('H-14')###
        for laser in lasers:
            print('H-14a')###
            print(undistort)
            print(calibration_data)
            print(undistort and calibration_data)
            laser_image = imtools.imread(folder+'/laser%d_%03d.%s'%(laser, n, settings.FILEFORMAT), format="rgb", calibrated=undistort and calibration_data)
            print('H-14b')###

            if laser_image is None:
                print('H-14c')###
                continue

            laser_grey = laser_image[:,:,RED]
            print('H-14d')###

            gui.progress("analyse", i, len(sequence))
            print('H-14e')###
            points, processed = lineprocessor(laser_image, laser_grey, fullcolor, ref_grey, laser_nr=laser,
                    mask=camera[i]['chess_contour'] if camera else None)
            print('H-14f')###

            # validate & store
            print('H-14g')###
            if points is not None and points[0].size:
                print('H-14h')###
                nosave = False
                if interactive:
                    print('H-14i')###
                    disp = cv2.merge( np.array(( laser_grey, processed, processed)) )
                    txt = "Esc=SKIP, Space=OK"
                    gui.display(disp, txt,  resize=True)
                pictures_todisplay.append((processed, laser_grey))
                if interactive:
                    print('H-14j')###
                    # detect the chess board
                    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.001)
                    found, corners = cv2.findChessboardCorners(ref_grey, settings.PATTERN_MATRIX_SIZE)
                    if found:
                        if not gui.ok_cancel(20):
                            nosave = True
                    else:
                        nosave = True

                if not interactive or not nosave:
                    print('H-14k')###
                    if camera:
                        print('H-14l')###
                        sliced_lines[n][laser] = [ points ] + camera[i]['plane']
                    else:
                        print('H-14m')###
                        sliced_lines[n][laser] = [ np.deg2rad(n), points, laser ]
                        if fullcolor is not None:
                            print('H-14n')###
                            color_slices[n][laser] = np.fliplr(fullcolor[(points[1], points[0])])

        # display
        print('H-15')###
        if i%int(settings.ui_base_i*2) == 0 and pictures_todisplay:
            if DEBUG:
                if len(pictures_todisplay) > 1:
                    pictures_todisplay = np.array(pictures_todisplay)
                    gref = cv2.addWeighted(pictures_todisplay[0,1], 0.5, pictures_todisplay[1,1], 0.5, 0)
                    nref = cv2.addWeighted(pictures_todisplay[0,0], 0.5, pictures_todisplay[1,0], 0.5, 0)
                else:
                    gref = pictures_todisplay[0][1]
                    nref = pictures_todisplay[0][0]

                nref = cv2.dilate(nref, d_kern).astype(np.uint8)
                r = cv2.bitwise_or(gref, nref)
                disp = cv2.merge( np.array(( r, gref, r)) )

                gui.display(disp, "lasers" if len(lasers) > 1 else "laser %d"%lasers[0],  resize=True)
            else:
                if len(pictures_todisplay) > 1:
                    gui.display(cv2.addWeighted(pictures_todisplay[1][1], 0.5, pictures_todisplay[0][1], 0.5, 0), "lasers" if len(lasers) > 1 else "laser %d"%lasers[0],  resize=True)
                else:
                    gui.display(pictures_todisplay[0][1], "lasers" if len(lasers) > 1 else "laser %d"%lasers[0],  resize=True)
        else:
            gui.redraw()
    print('H-16')###
    if len(sliced_lines) == 0:
        print('H-17')###
        raise AnalyseError("Unable to recognize lines in picture")
    if camera:
        yield sliced_lines
    else:
        yield sliced_lines, color_slices
