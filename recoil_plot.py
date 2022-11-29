import json
import math
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from itertools import pairwise
from numpy import float32
from numpy.linalg import norm

RESOLUTION_X = 1920
RESOLUTION_Y = 1080
VIEWPORT = [-RESOLUTION_X/2, RESOLUTION_X/2, -RESOLUTION_Y/2, RESOLUTION_Y/2]

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
    return bezier(*(lerp(*p, t) for p in pairwise([a, *b])), t=t) if b else a

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

def get_pattern(gun, start=0, end=1000, *, flip=False, subdivs=1):
    stability = gun.Stability
    yaw_manipulator = stability.YawDirectionManipulator
    flip_time = 0.0

    start = int(start)
    end   = min(int(end), gun.MagazineAmmo.MaxAmmo)

    for n in range(start * subdivs, (end - 1) * subdivs + 1):
        bullet = n / subdivs
        pitch  = eval_curve(stability.PitchRecoil.FiringCurve, bullet)
        yaw    = eval_curve(stability.YawRecoil.FiringCurve,   bullet)

        if flip and bullet >= yaw_manipulator.ProtectedBulletCount:
            fraction = flip_time / yaw_manipulator.TimeToSwitchYaw
            yaw *= smooth_step(1, -1, min(fraction, 1))
            flip_time += 1 / gun.FiringState.FiringRate / subdivs

        yield (pitch, yaw)

def deg_to_mil(degrees):
    return math.tan(degrees * math.pi/180) * 1000

def spray_to_mil(pattern):
    return [(deg_to_mil(yaw), deg_to_mil(pitch)) for pitch, yaw in pattern]

def deg_to_px(degrees):
    return math.tan(degrees * math.pi/180) / HALF_VFOV_TAN * RESOLUTION_Y/2

def spray_to_px(pattern):
    return [(deg_to_px(yaw), deg_to_px(pitch)) for pitch, yaw in pattern]

def invert(points):
    return [[-x for x in p] for p in points]

def split_axes(points):
    return [[p[n] for p in points] for n in range(len(points[0]))]

def main():
    in_path = sys.argv[1]

    with open(in_path, "r") as file:
        gun = json.load(file, object_hook=lambda obj: JsonHook(obj))

    plt.rc('lines', linewidth=0.5, markersize=1, markeredgewidth=0)

    plt.axis('off')
    plt.subplots_adjust(0, 0, 1, 1, 0, 0)

    plt.imshow(plt.imread("recoil_bg.png"), extent=VIEWPORT)
    plt.axhspan(*VIEWPORT[2:4], *VIEWPORT[0:2], color='0', alpha=0.8)

    spray = spray_to_px(get_pattern(gun, subdivs=10))
    flip  = spray_to_px(get_pattern(gun, subdivs=10, flip=True))
    spray_closed = [*spray, sorted(spray, key=lambda p: p[1])[-1]]
    flip_closed  = [*flip,  sorted(flip,  key=lambda p: p[1])[-1]]
    spray_x, spray_y = split_axes(invert(spray_closed))
    flip_x,  flip_y  = split_axes(invert(flip_closed))
    plt.fill_betweenx(spray_y, spray_x, flip_x, facecolor='1', alpha=0.25)

    flip_start = int(gun.Stability.YawDirectionManipulator.ProtectedBulletCount)

    spray = spray_to_px(get_pattern(gun, subdivs=10))
    flip  = spray_to_px(get_pattern(gun, flip_start, subdivs=10, flip=True))
    plt.plot(*split_axes(invert(flip)),  color='#13AFC0', alpha=0.5)
    plt.plot(*split_axes(invert(spray)), color='#FF7F00', alpha=0.5)

    spray = spray_to_px(get_pattern(gun))
    flip  = spray_to_px(get_pattern(gun, flip_start, flip=True))
    plt.plot(*split_axes(invert(flip)),  "o", color='#13AFC0')
    plt.plot(*split_axes(invert(spray)), "o", color='#FF7F00')

    plt.autoscale()
    plt.gca().set_xbound(-256, 256)
    plt.gca().set_ybound(-256, 256)

    out_path = get_output_path(in_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', pad_inches=0)
    print(f"Wrote to \"{out_path}\"")

if __name__ == "__main__":
    main()