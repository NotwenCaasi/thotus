from thotus import settings
from thotus.cloudify import cloudify
from thotus.mesh import meshify

import numpy as np

try:
    from scipy.sparse import linalg
except ImportError:
    def svd(M):
        return np.linalg.svd(M)[0][:,2]
else:
    def svd(M):
        return linalg.svds(M, k=2)[0]

def find_laser_plane(X):
    n = X.shape[0]
    Xm = X.sum(axis=0) / n
    M = np.array(X - Xm).T
    U = svd(M)
    normal = np.cross(U.T[0], U.T[1])
    if normal[2] < 0:
        normal *= -1

    dist = np.dot(normal, Xm)
    std = np.dot(M.T, normal).std()
    return (dist, normal, std)

def calibration(calibration_data, calibration_settings, images, interactive=True):
    print('G-10')###
    tot_deviation = 0.0
    for laser in settings.get_laser_range():
        print('G-11')###
        selected_planes = []
        ranges = []
        for fn in images:
            print('G-12')###
            num = int(fn.rsplit('/')[-1].split('_')[1].split('.')[0])
            if laser == 0:
                if num > 80:
                    continue
            else:
                if num < 20:
                    continue
            ranges.append(num)
            selected_planes.append(fn)

        print('G-13')###
        im = [calibration_settings[x] for x in selected_planes]
        print('G-14')###

        assert len(ranges) == len(im)

        print('G-15')###
        slices = cloudify(calibration_data, settings.CALIBDIR, [laser], ranges,
                method='straighttralala', camera=im, interactive=interactive, undistort=True)

        print('G-16')###
        obj = meshify(calibration_data, slices, camera=im, cylinder=(1000, 1000))

        print('G-17')###
        dist, normal, std = find_laser_plane(np.array(obj.vertices))
        print('G-18')###
        tot_deviation += std
        print('G-19')###
        print("\nLaser %d deviation: %.2f"%(laser+1, std))

        print('G-20')###
        calibration_data.laser_planes[laser].normal = normal
        print('G-21')###
        calibration_data.laser_planes[laser].distance = dist
        print('G-22')###
        obj.save("laser%d.ply"%laser)
        print('G-23')###

    tot_deviation /= 2
    if tot_deviation < 0.01:
        txt = ("Perfect !!")
    elif tot_deviation < 0.05:
        txt = ("Excellent !")
    elif tot_deviation < 0.1:
        txt = ("Good :)")
    elif tot_deviation < 0.3:
        txt = ("Expect shift between lasers :(")
    else:
        txt = ("Consider recalibrating, result is very bad")

    print("\nDeviation is %.2f. %s"%(tot_deviation, txt))

