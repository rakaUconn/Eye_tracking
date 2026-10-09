import numpy as np, sys, json
import simulate_images as SI
rng = np.random.default_rng(5); out = {}
poses = [(tx, ty) for tx in (-10, 0, 10) for ty in (-10, 0, 10)]
for dz in (-2, -1, -0.5, 0, 0.5, 1, 2):
    ok = 0; n = 0; errs = []
    for tx, ty in poses:
        p1, p4 = SI.gaze_glints("L", tx, ty); sh = np.array([0, 0, dz])
        for rep in range(3):
            dn, tr = SI.render({"L": (p1+sh, p4+sh)}, noise=True, rng=rng); dt = SI.detect(dn, "L"); n += 1
            t4 = np.array(tr["L"]["P4"])
            if dt["P4"] is not None and np.hypot(*(np.array(dt["P4"])-t4)) < 2.0: ok += 1; errs.append(np.hypot(*(np.array(dt["P4"])-t4)))
    out[dz] = dict(detect_rate=ok/n, p4_centroid_err_px=float(np.mean(errs)) if errs else None)
    print(dz, out[dz], flush=True)
json.dump(out, open(f"../results/detect_vs_depth{SI.SUF}.json", "w"), indent=1)
