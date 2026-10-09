"""Depth-of-field and quick Monte-Carlo tolerance check for design JSONs (Design 3 vs new finalists).
usage: python3 tol_depth.py design3_final design4A ...   -> ../results/tol_depth.json"""
import sys, json, numpy as np
import fastchan as FC
from raytrace import Surf
BUILD0 = FC.build

def load(name):
    P = json.load(open(f'../results/{name}.json'))
    return [tuple(c) for c in P['cfg']], P['ts'], np.atleast_1d(P['gap']), P['b'], P['Lo'], P['D'] / 2, P['half']

def depth(name):
    cfg, ts, g, b, Lo, r, half = load(name); out = []
    for dz in (-2, -1, -0.5, 0, 0.5, 1, 2):     # + = eye farther from camera
        res = FC.metrics(cfg, ts, g, b, Lo + dz, r, half, n=16)
        out.append((dz, round(float(res['rms'].mean()), 2), round(float(res['rms'].max()), 2)))
    return out

def perturbed_build(cfg, ts, gaps, b, r, half, rng, dg=0.2, dc=0.1, defl=0.01):
    S, zs, lz = BUILD0(cfg, ts, gaps, b, r, half)
    # spacing errors: shift every element after k by cumulative error; decenter each element; radius scale (~EFL)
    shifts = np.cumsum(np.r_[rng.uniform(-dg, dg), rng.uniform(-dg, dg, len(cfg) - 1)])
    S2 = S[:3]; k = 3
    for e, (z0, z1, el, dia) in enumerate(lz):
        dx = rng.uniform(-dc, dc); sc = 1 + rng.uniform(-defl, defl)
        for _ in el:
            s = S[k]; S2.append(Surf(s.z + shifts[e], s.R * sc, s.after, x0=dx, ap=(dx, 0, s.ap[2]))); k += 1
    S2 += S[k:]
    return S2, zs

def mc(name, N=60, seed=3):
    cfg, ts, g, b, Lo, r, half = load(name)
    rng = np.random.default_rng(seed); orig = FC.build; res = []
    for i in range(N):
        def fake(cfg_, ts_, gaps_, b_, r_, half_, _i=i):
            rr = np.random.default_rng(seed * 1000 + _i)       # same perturbation for every refocus call
            S2, zs = perturbed_build(cfg_, ts_, gaps_, b_, r_, half_, rr)
            return S2, zs, BUILD0(cfg_, ts_, gaps_, b_, r_, half_)[2]
        FC.build = fake
        try:
            best = None
            for db in np.arange(-1.5, 1.51, 0.1):        # refocus (camera rail)
                q = FC.metrics(cfg, ts, g, b + db, Lo, r, half, n=10)
                if q is None: continue
                c = q['rms'].mean() + 0.3 * q['rms'].max()
                if best is None or c < best[0]: best = (c, db)
            q = FC.metrics(cfg, ts, g, b + best[1], Lo, r, half, n=14)
            res.append((float(q['rms'].mean()), float(q['rms'].max()), float(q['m'])))
        finally:
            FC.build = orig
    a = np.array(res)
    return dict(mean_p50=float(np.median(a[:, 0])), mean_p90=float(np.percentile(a[:, 0], 90)),
                max_p50=float(np.median(a[:, 1])), max_p90=float(np.percentile(a[:, 1], 90)),
                m_std=float(a[:, 2].std()))

if __name__ == "__main__":
    out = {}
    for nm in sys.argv[1:]:
        out[nm] = dict(depth=depth(nm), mc=mc(nm))
        print(nm, json.dumps(out[nm]), flush=True)
    json.dump(out, open('../results/tol_depth.json', 'w'), indent=1)
