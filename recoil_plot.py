import json
import math
import sys
import matplotlib.pyplot as plt
from itertools import pairwise, tee
from numpy import float32

SCALE = 180
ONE_THIRD = float32(1) / float32(3)

class JsonHook(dict):
    def __getattr__(self, name):
        match self[name]:
            case float(f): return float32(f)
            case value:    return value

def lerp(a, b, t):
    return a + (b - a) * t

def bezier(P0, *PN, t):
    return bezier(*(lerp(*p,t) for p in pairwise([P0,*PN])), t=t) if PN else P0

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

def round32(f):
    return next((r for r in (round(float(f), n) for n in range(8))
                         if float32(f) == float32(r)), f)

def smooth_step(a, b, t):
    return lerp(a, b, (3 - 2*t) * t*t)

def get_spray_pattern(gun, start=0, end=1000, *, flip=False):
    stability = gun.Stability
    yaw_manipulator = stability.YawDirectionManipulator
    flip_time = 0.0

    for bullet in range(int(start), min(int(end), gun.MagazineAmmo.MaxAmmo)):
        pitch = eval_curve(stability.PitchRecoil.FiringCurve, bullet)
        yaw   = eval_curve(stability.YawRecoil.FiringCurve,   bullet)

        if flip and bullet >= yaw_manipulator.ProtectedBulletCount:
            fraction = flip_time / yaw_manipulator.TimeToSwitchYaw
            yaw *= smooth_step(1, -1, min(fraction, 1))
            flip_time += 1 / gun.FiringState.FiringRate

        yield (pitch, yaw)

def deg_to_mil(degrees):
    return math.tan(degrees * math.pi/180) * 1000

def spray_to_mil(pattern):
    return [(deg_to_mil(yaw), deg_to_mil(pitch)) for pitch, yaw in pattern]

def split_axes(points):
    return [[p[n] for p in points] for n in range(len(points[0]))]

def main():
    with open(sys.argv[1], "r") as file:
        gun = json.load(file, object_hook=lambda obj: JsonHook(obj))

    for bullet, (pitch, yaw) in enumerate(get_spray_pattern(gun)):
        print(f"{bullet:2d} recoil ({round32(pitch):.7f}, {round32(yaw):.7f})")

    pattern = spray_to_mil(get_spray_pattern(gun))
    flipped = spray_to_mil(get_spray_pattern(gun, flip=True))

    pattern_highest = sorted(pattern, key=lambda p: p[1])[-1]
    flipped_highest = sorted(flipped, key=lambda p: p[1])[-1]
    pattern_x, pattern_y = split_axes([*pattern, pattern_highest])
    flipped_x, flipped_y = split_axes([*flipped, flipped_highest])
    plt.fill_betweenx(pattern_y, pattern_x, flipped_x, alpha=0.5)

    plt.plot(flipped_x[:-1], flipped_y[:-1], "-o")
    plt.plot(pattern_x[:-1], pattern_y[:-1], "-o")

    plt.axis([-SCALE / 2, SCALE / 2, 0, SCALE])
    plt.gca().set_aspect('equal')
    plt.show()

if __name__ == "__main__":
    main()