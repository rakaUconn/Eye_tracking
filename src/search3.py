"""Beam extension: add a third stock element (any type/orientation/position) to the best pairs, at stop diameter D, eye->first lens 195-205 mm."""
import sys, json, glob, numpy as np
from multiprocessing import Pool
from scipy.optimize import minimize
from raytrace import Surf
import stock_final as SF
from stock import element, LIB
from channel import fields
D = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0
HALF = max(6.5, D/2 + 0.3)
FILT_T = SF.FILT_T

def build_multi(ts, gaps, b):
    gaps = np.atleast_1d(gaps)
    S = [Surf(0.0, kind="stop", ap=(SF.XC, 0, SF.SR)), Surf(0.0, np.inf, SF.FILT_G), Surf(FILT_T, np.inf, "air")]
    z = FILT_T + ts
    for k, (name, flip) in enumerate(SF.CFG):
        el, dia = element(name, flip)
        for R, t, med in el:
            S.append(Surf(z, R, med, ap=(0, 0, 0.45*dia))); z += t
        if k < len(SF.CFG)-1: z += gaps[min(k, len(gaps)-1)]
    zc = z + b
    S += [Surf(zc, np.inf, "N-BK7"), Surf(zc+SF.COVER_T, np.inf, "air")]
    return S, zc + SF.COVER_T + SF.COVER_GAP

def cost(u, F, n, ng):
    ts, b = u[0], u[-1]; gaps = u[1:1+ng]; Lo = u[1+ng]
    if not (0.3 <= ts <= 12 and np.all(gaps >= 0.3) and np.all(gaps <= 80) and 150 <= Lo <= 215 and 30 <= b <= 170 and 195 <= Lo + FILT_T + ts <= 205): return 1e6
    try: r = SF.metrics((ts, gaps, b), Lo, F=F, n=n)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr, _ = r
    return (rms*1e3).mean() + 0.3*rms.max()*1e3 + 1500*max(0, abs(m-0.56)-0.03) + 150*(1-fr).max() + 300*max(0, 0.3-c[:, 0].min()) + 300*max(0, c[:, 0].max()-9.3)

def job(cfg):
    SF.build = build_multi; SF.CFG = cfg; SF.SR = D/2; SF.XC = -HALF
    F = fields(n=3, ex=11.6, ey=15.2, xc=-HALF); ng = len(cfg)-1
    bs = np.arange(30, 170, 8.0); best = None
    for g0 in (3.0,):
        cs = [cost(np.r_[1.0, [g0]*ng, 196.0, b], F, 8, ng) for b in bs]
        if min(cs) >= 1e6: continue
        u = np.r_[1.0, [g0]*ng, 196.0, bs[int(np.argmin(cs))]]
        for it in range(2):
            q = minimize(cost, u, args=(F, 8, ng), method="Nelder-Mead", options=dict(maxiter=150*(ng+1), xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
        if best is None or q.fun < best[0]: best = (q.fun, u.tolist())
    return dict(cfg=cfg, cost=(best[0] if best else 1e6), u=(best[1] if best else None))

if __name__ == "__main__":
    # base pairs from the 200 mm search
    rows = []
    for f in glob.glob('../results/stock200_[0-3].json'): rows += json.load(open(f))
    rows = [r for r in sorted(rows, key=lambda r: r['cost']) if len(r['cfg']) == 2][:2]
    bases = [[tuple(c) for c in r['cfg']] for r in rows]
    names = [n for n in LIB if n.startswith(('LC','LD','LF','LE1','LE1234','LBF','LA12','LA11','LB1294','LB1471'))]; cand = []
    for n in names:
        for fl in (0, 1):
            if n in ("LB1471", "LB1294", "LB1199", "LD1613", "LD1464") and fl == 1: continue
            cand.append((n, fl))
    cfgs = []
    for base in bases:
        for pos in range(3):
            for c in cand: cfgs.append(base[:pos] + [c] + base[pos:])
    print(len(cfgs), "configs, D =", D, flush=True)
    out = []
    with Pool(4) as p:
        for r in p.imap_unordered(job, cfgs, chunksize=2):
            out.append(r); print(json.dumps(dict(cfg=r['cfg'], cost=round(r['cost'], 1), u=None if r['u'] is None else np.round(r['u'], 2).tolist())), flush=True)
            json.dump(out, open(f"../results/search3_D{int(D)}.json", "w"))
