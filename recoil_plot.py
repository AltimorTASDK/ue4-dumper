import json
import math
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from itertools import pairwise
from matplotlib.transforms import Bbox
from numpy import array, float32, linalg

VIEWPORT_X = 1920
VIEWPORT_Y = 1080
VIEWPORT   = [-VIEWPORT_X/2, VIEWPORT_X/2, -VIEWPORT_Y/2, VIEWPORT_Y/2]
ZOOM       = 1
CROP       = array([256, 256]) * ZOOM
DPI        = 300 * ZOOM

SHOW_ERROR = False

HALF_VFOV_TAN = math.tan(45 * math.pi/180) * 3/4

ONE_THIRD = float32(1) / float32(3)

class JsonHook(dict):
    def __getattr__(self, name):
        match self[name]:
            case float(f): return float32(f)
            case value:    return value

def get_output_path(path):
    """Generate an output path."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    guns_dir = os.path.join(script_dir, "guns")
    path = os.path.realpath(path)

    if os.path.commonpath([guns_dir, os.path.realpath(path)]) == guns_dir:
        subpath = os.path.relpath(path, guns_dir)
    else:
        subpath = os.path.basename(path)

    return os.path.join(script_dir, "recoil",
                        f"{os.path.splitext(subpath)[0]}.png")

def lerp(a, b, t):
    return a + (b - a) * t

def bezier(a, *b, t):
    return bezier(*(lerp(*p, t) for p in zip([a, *b], b)), t=t) if b else a

def eval_curve(curve, time):
    time = float32(time)

    if time <= curve[0].Time:
        return curve[0].Value
    if time >= curve[-1].Time:
        return curve[-1].Value

    key1, key2 = next(filter(lambda pair: pair[1].Time > time, pairwise(curve)))
    delta = key2.Time - key1.Time
    alpha = (time - key1.Time) / delta

    match key1.InterpMode:
        case 'RCIM_Constant':
            return key1.Value
        case 'RCIM_Linear':
            return lerp(key1.Value, key2.Value, alpha)
        case 'RCIM_Cubic':
            return bezier(key1.Value,
                          key1.Value + (key1.LeaveTangent  * delta * ONE_THIRD),
                          key2.Value - (key2.ArriveTangent * delta * ONE_THIRD),
                          key2.Value,
                          t=alpha)

def smooth_step(a, b, t):
    return lerp(a, b, (3 - 2*t) * t*t)

def deg_to_mil(degrees):
    return math.tan(degrees * math.pi/180) * 1000

def deg_to_px(degrees):
    return math.tan(degrees * math.pi/180) / HALF_VFOV_TAN * VIEWPORT_Y/2

def get_pattern(gun, start=None, end=None, *, flip=False, subdivs=1,
                units='px', half=True, invert=True):
    stability       = gun.Stability
    yaw_manipulator = stability.YawDirectionManipulator
    flip_time       = 0.0

    if start is None:
        start = int(yaw_manipulator.ProtectedBulletCount + 1) if flip else 0

    if end is None:
        end = int(gun.MagazineAmmo.MaxAmmo)

    pattern = []

    for n in range(start * subdivs, (end - 1) * subdivs + 1):
        bullet = n / subdivs
        pitch  = eval_curve(stability.PitchRecoil.FiringCurve, bullet)
        yaw    = eval_curve(stability.YawRecoil.FiringCurve,   bullet)

        if flip and bullet >= yaw_manipulator.ProtectedBulletCount + 1:
            fraction = flip_time / yaw_manipulator.TimeToSwitchYaw
            yaw *= smooth_step(1, -1, min(fraction, 1))
            flip_time += 1 / gun.FiringState.FiringRate / subdivs

        if invert: pitch, yaw = -pitch,   -yaw
        if half:   pitch, yaw =  pitch/2,  yaw/2

        match units:
            case 'deg': pattern.append((pitch, yaw))
            case 'mil': pattern.append((deg_to_mil(yaw), deg_to_mil(pitch)))
            case 'px':  pattern.append((deg_to_px (yaw), deg_to_px (pitch)))
            case _:     raise ValueError

    return array(pattern)

def get_error(gun, start=0, end=None, *, subdivs=1, units='px'):
    if end is None:
        end = int(gun.MagazineAmmo.MaxAmmo)

    curve = []

    for n in range(start * subdivs, (end - 1) * subdivs + 1):
        bullet = n / subdivs
        error = eval_curve(gun.Stability.Error.FiringCurve, bullet)

        match units:
            case 'deg': curve.append(error)
            case 'mil': curve.append(deg_to_mil(error))
            case 'px':  curve.append(deg_to_px (error))
            case _:     raise ValueError

    return array(curve)

def line_intersection(a, b):
    try:
        return linalg.solve(array([a[1]-a[0], b[0]-b[1]]).T, b[0]-a[0])
    except linalg.LinAlgError:
        return None

def fix_overlap(points):
    i = 0
    result = []
    while i < len(points) - 1:
        low_t = 1
        closest = None
        for j in range(len(points) - 1):
            if (t := line_intersection(points[i:i+2], points[j:j+2])):
                t[0]

def dump_plot(in_path):
    with open(in_path, "r") as file:
        gun = json.load(file, object_hook=JsonHook)

    plt.clf()

    plt.rc('lines', linewidth=0.5/ZOOM, markersize=1/ZOOM, markeredgewidth=0)

    plt.imshow(plt.imread("recoil_bg.png"), extent=VIEWPORT)
    plt.axhspan(*VIEWPORT[2:4], *VIEWPORT[0:2], color='0', alpha=0.75)

    spray = get_pattern(gun, 0, subdivs=10, flip=False)
    flip  = get_pattern(gun, 0, subdivs=10, flip=True )
    spray = array([*spray, spray[spray[:,1].argsort()[0]]]).T
    flip  = array([*flip,  flip [flip [:,1].argsort()[0]]]).T
    plt.fill_betweenx(spray[1], spray[0], flip[0], fc='1', alpha=0.25)

    plt.plot(*get_pattern(gun, subdivs=10, flip=True ).T, c='#13AFC07F')
    plt.plot(*get_pattern(gun, subdivs=10, flip=False).T, c='#FF7F007F')

    plt.plot(*get_pattern(gun, flip=True ).T, "o", c='#13AFC0')
    plt.plot(*get_pattern(gun, flip=False).T, "o", c='#FF7F00')

    if SHOW_ERROR:
        error_end = int(gun.Stability.Error.FiringCurve[-1].Time) + 1
        error = get_error(gun, 0, error_end)
        plt.plot(error, np.zeros(error_end),      c='#FF00FF7F')
        plt.plot(error, np.zeros(error_end), "o", c='#FF00FF')

    plt.axis('off')
    plt.subplots_adjust(0, 0, 1, 1)
    plt.autoscale()

    tight_bbox = plt.gcf().get_tightbbox()
    center = (tight_bbox.min + tight_bbox.max) / 2
    bbox = Bbox([center - CROP/DPI/2, center + CROP/DPI/2])

    out_path = get_output_path(in_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=DPI, bbox_inches=bbox)
    print(f"Wrote to \"{out_path}\"")

def main():
    for path in sys.argv[1:]:
        dump_plot(path)

if __name__ == "__main__":
    main()