import json
import os
import sys
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from recoil_plot import *

# seems to be bezier curve with
# t0 = 0
# t1 = N
# p0 = 1/TapEfficiency
# p3 = 1
# m0 = (N/2 - 1/TapEfficiency)/(N/2)
# m1 = 1
#
# where N is shots fired

# sheriff graph https://www.desmos.com/calculator/zhdejitpgh
# ghost https://www.desmos.com/calculator/0jxm0o9hyx

# single tap
#SHERIFF = np.array([[0.25, 1.94], [0.28, 1.94], [0.33, 1.95],
#                    [0.38, 1.96], [0.42, 1.99], [0.47, 2.02],
#                    [0.52, 2.06], [0.57, 2.11], [0.62, 2.16],
#                    [0.67, 2.22], [0.71, 2.29], [0.76, 2.36],
#                    [0.81, 2.43], [0.86, 2.51], [0.91, 2.58],
#                    [0.96, 2.64], [1.00, 2.70], [1.05, 2.74]])

# double tap
#SHERIFF = np.array([[0.33, 2.02], [0.41, 2.09], [0.48, 2.17], [0.56, 2.25],
#                    [0.64, 2.33], [0.72, 2.41], [0.80, 2.48], [0.88, 2.55],
#                    [0.95, 2.61], [1.03, 2.67], [1.11, 2.71], [1.19, 2.74]])

# triple tap
SHERIFF = np.array([[0.29, 1.11], [0.33, 1.15], [0.37, 1.20], [0.41, 1.27],
                    [0.45, 1.34], [0.48, 1.43], [0.52, 1.53], [0.56, 1.64],
                    [0.60, 1.75], [0.64, 1.86], [0.68, 1.98], [0.72, 2.09],
                    [0.76, 2.20], [0.80, 2.31], [0.84, 2.41], [0.88, 2.50],
                    [0.91, 2.58], [0.95, 2.64], [0.99, 2.70], [1.03, 2.73],
                    [1.07, 2.75]])

# single tap
GHOST = np.array([[0.30, 0.72], [0.33, 0.73], [0.36, 0.75], [0.39, 0.78],
                  [0.42, 0.81], [0.44, 0.84], [0.47, 0.88], [0.50, 0.92],
                  [0.53, 0.96], [0.56, 1.01], [0.59, 1.06], [0.62, 1.12],
                  [0.65, 1.18]])

# double tap
JUDGE = np.array([[2.37, 3.04], [2.42, 3.08], [2.46, 3.12], [2.51, 3.17],
                  [2.65, 3.33], [2.69, 3.38], [2.74, 3.43], [2.79, 3.46],
                  [2.83, 3.49], [2.88, 3.50], [2.97, 3.54], [3.02, 3.57],
                  [3.11, 3.66], [3.16, 3.71], [3.20, 3.76], [3.25, 3.81],
                  [3.29, 3.86], [3.34, 3.91], [3.39, 3.94], [3.43, 3.97]])

# single tap
#HEADHUNTER = np.array([[0.00, 1.15], [0.04, 1.18], [0.10, 1.24],
#                       [0.16, 1.32], [0.23, 1.41], [0.29, 1.51],
#                       [0.35, 1.61], [0.41, 1.73], [0.48, 1.85],
#                       [0.54, 1.97], [0.60, 2.10], [0.66, 2.22],
#                       [0.73, 2.34], [0.79, 2.45], [0.85, 2.55],
#                       [0.91, 2.63], [0.98, 2.69], [1.04, 2.74]])

# double tap
HEADHUNTER = np.array([[0.09, 1.22], [0.17, 1.31], [0.26, 1.41], [0.34, 1.53],
                       [0.43, 1.66], [0.52, 1.79], [0.60, 1.93], [0.69, 2.08],
                       [0.77, 2.21], [0.86, 2.34], [0.95, 2.46], [1.03, 2.56],
                       [1.12, 2.65], [1.20, 2.71], [1.29, 2.74]])

def get_mapping(curve, samples):
    SUBDIVS = 10000
    mapping = [(x, (-1, -1)) for x in samples]

    for n in range(int(curve[-1].Time) * SUBDIVS + 1):
        bullet = n / SUBDIVS
        error = eval_curve(curve, bullet)
        for i, (key, (old_x, old_y)) in enumerate(mapping):
            if abs(error - key) < abs(old_y - key):
                mapping[i] = (key, (bullet, error))


    return [(bullet, error) for (error, (bullet, _)) in mapping]

def main():
    in_path = sys.argv[1]

    with open(in_path, "r") as file:
        gun = json.load(file, object_hook=JsonHook)

    samples = {
        'Revolver.json':    SHERIFF,
        'Luger.json':       GHOST,
        'AutoShotgun.json': JUDGE,
        'Gun.json':         HEADHUNTER,
    }[os.path.basename(in_path)]

    if samples is HEADHUNTER:
        curve = gun.ZoomedStability.Error.FiringCurve
    else:
        curve = gun.Stability.Error.FiringCurve

    if False:
        map1_lo = get_mapping(curve, [max(x, 0) for x in samples[:,0] - 0.005])
        map1_hi = get_mapping(curve, [max(x, 0) for x in samples[:,0] + 0.005])

        map2_lo = get_mapping(curve, [max(x, 0) for x in samples[:,1] - 0.005])
        map2_hi = get_mapping(curve, [max(x, 0) for x in samples[:,1] + 0.005])

        print("\n".join(f"({x1l:.4f}~{x1h:.4f}, {y1 + 0.005:.2f}), "
                        f"({x2l:.4f}~{x2h:.4f}, {y2 + 0.005:.2f})"
                        for (x1l, y1), (x1h, _), (x2l, y2), (x2h, _)
                        in zip(map1_lo, map1_hi, map2_lo, map2_hi)))
    else:
        map1 = get_mapping(curve, samples[:,0])
        map2 = get_mapping(curve, samples[:,1])

        print("\n".join(f"({x1:.4f}, {y1:.2f}), ({x2:.4f}, {y2:.2f})"
                        for (x1, y1), (x2, y2) in zip(map1, map2)))

if __name__ == "__main__":
    main()