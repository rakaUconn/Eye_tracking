"""Stock search at eye->stop ~200 mm (195-205), final layout model (filter at stop, cover on sensor)."""
import sys, json, itertools, numpy as np
from scipy.optimize import minimize
import stock_final as SF
from stock import LIB
NAMES = ["AC254-050","AC254-075-B","AC254-150","AC508-150-B","LBF254-050","LBF254-100","LBF254-200","LB1471","LA1131","LE1234","LE1104","LA1229"]
LOLO, LOHI = 195., 205.
def cost(u):
    ts, gap, Lo, b = u
    if not (0.3 <= ts <= 10 and 0.3 <= gap <= 60 and LOLO <= Lo <= LOHI and 30 <= b <= 160): return 1e6
    try: r = SF.metrics((ts, gap, b), Lo, n=8)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr, _ = r
    return (rms*1e3).mean()+0.3*rms.max()*1e3+1500*abs(m-0.55)+150*(1-fr).max()
def feasible(cfg):
    f = [LIB[n][0] for n, _ in cfg]
    if len(f) == 1: return 55 <= f[0] <= 100
    f1, f2 = f; lo, hi = 1/(1/f1+1/f2), 1/(1/f1+1/f2-0.0)   # at d=0
    good = any(f1+f2-d > 0 and 62 <= f1*f2/(f1+f2-d) <= 82 for d in np.linspace(0, 30, 13))
    names = [n for n, _ in cfg]
    return good and any(n.startswith(('AC', 'LBF')) for n in names)
if __name__ == "__main__":
    part = int(sys.argv[1]); opts = [(n, fl) for n in NAMES for fl in (0, 1)]
    cfgs = [[o] for o in opts] + [[a, b] for a in opts for b in opts]
    cfgs = [c for c in cfgs if feasible(c)][part::4]; res = []
    for cfg in cfgs:
        SF.CFG = cfg; best = None
        for gap0 in ((1.0,) if len(cfg) == 1 else (1.0, 15.0)):
            # coarse focus scan over b
            bs = np.arange(30, 150, 6.0); cs = [cost([1.0, gap0, 200., b]) for b in bs]; b0 = bs[int(np.argmin(cs))]
            u = np.array([1.0, gap0, 200., b0])
            for it in range(2):
                q = minimize(cost, u, method="Nelder-Mead", options=dict(maxiter=160, xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
            if best is None or q.fun < best[0]: best = (q.fun, u.tolist())
        res.append(dict(cfg=cfg, cost=best[0], u=best[1])); print(cfg, round(best[0], 1), np.round(best[1], 1), flush=True)
        json.dump(res, open(f"../results/stock200_{part}.json", "w"))
