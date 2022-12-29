import json
import os
import sys
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from recoil_plot import *


SHERIFF = np.array([[0.25, 1.94], [0.28, 1.94], [0.33, 1.95],
                    [0.38, 1.96], [0.42, 1.99], [0.47, 2.02],
                    [0.52, 2.06], [0.57, 2.11], [0.62, 2.16],
                    [0.67, 2.22], [0.71, 2.29], [0.76, 2.36],
                    [0.81, 2.43], [0.86, 2.51], [0.91, 2.58],
                    [0.96, 2.64], [1.00, 2.70], [1.05, 2.74]])

GHOST = np.array([[0.30, 0.72], [0.33, 0.73], [0.36, 0.75],
                  [0.39, 0.78], [0.44, 0.84], [0.47, 0.88],
                  [0.50, 0.92], [0.53, 0.96], [0.56, 1.01],
                  [0.59, 1.06], [0.62, 1.12], [0.65, 1.18]])

JUDGE = np.array([[2.37, 3.04], [2.42, 3.08], [2.46, 3.12], [2.51, 3.17],
                  [2.65, 3.33], [2.69, 3.38], [2.74, 3.43], [2.79, 3.46],
                  [2.83, 3.49], [2.88, 3.50], [2.97, 3.54], [3.02, 3.57],
                  [3.11, 3.66], [3.16, 3.71], [3.20, 3.76], [3.25, 3.81],
                  [3.29, 3.86], [3.34, 3.91], [3.39, 3.94], [3.43, 3.97]])

# double tap
#HEADHUNTER = np.array([[0.09, 1.22], [0.17, 1.31], [0.26, 1.41], [0.34, 1.53],
#                       [0.43, 1.66], [0.52, 1.79], [0.60, 1.93], [0.69, 2.08],
#                       [0.77, 2.21], [0.86, 2.34], [0.95, 2.46], [1.12, 2.65],
#                       [1.20, 2.71]])

# single tap
HEADHUNTER = np.array([[0.00, 1.15], [0.04, 1.18], [0.10, 1.24],
                       [0.16, 1.32], [0.23, 1.41], [0.29, 1.51],
                       [0.35, 1.61], [0.41, 1.73], [0.48, 1.85],
                       [0.54, 1.97], [0.60, 2.10], [0.66, 2.22],
                       [0.73, 2.34], [0.79, 2.45], [0.85, 2.55],
                       [0.91, 2.63], [0.98, 2.69], [1.04, 2.74]])

def get_mapping(curve, samples):
    SUBDIVS = 10000

    mapping = [(x, (-1, -1)) for x in samples]
    end = int(curve[-1].Time) * SUBDIVS + 1

    for n in range(end):
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

    map1_lo = get_mapping(curve, [max(x, 0) for x in samples[:,0] - 0.005])
    map1_hi = get_mapping(curve, [max(x, 0) for x in samples[:,0] + 0.005])

    map2_lo = get_mapping(curve, [max(x, 0) for x in samples[:,1] - 0.005])
    map2_hi = get_mapping(curve, [max(x, 0) for x in samples[:,1] + 0.005])

    print("\n".join(f"({x1l:.4f}~{x1h:.4f}, {y1:.2f}), "
                    f"({x2l:.4f}~{x2h:.4f}, {y2:.2f})"
                    for (x1l, y1), (x1h, _), (x2l, y2), (x2h, _)
                    in zip(map1_lo, map1_hi, map2_lo, map2_hi)))
    return

if __name__ == "__main__":
    main()