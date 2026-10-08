import json, glob, numpy as np, opt_stock as O
from scipy.optimize import minimize
rows = []
for f in glob.glob('../results/stock_search_*.json'): rows += json.load(open(f))
rows = sorted(rows, key=lambda r: r['cost']); print(len(rows), "configs")
for r in rows[:8]: print(round(r['cost'],1), r['cfg'])
def cost(u, cfg):
    ts, gap, Lo, dz = u
    if not (0 <= ts <= 40 and 0 <= gap <= 120 and 120 <= Lo <= 175 and abs(dz) < 8): return 1e6
    try:
        S, zl = O.build(cfg, ts, gap); r = O.metrics(cfg, ts, gap, Lo, O.para_focus(S, zl, Lo)+dz)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr = r
    return (rms*1e3).mean()+0.3*rms.max()*1e3+2000*abs(m-O.M_T)+150*(1-fr).max()
out = []
for r in rows[:6]:
    cfg = [tuple(c) for c in r['cfg']]; best = None
    for Lo0 in (135., 149.4, 165.):
        for gap0 in (0.0, 5.0, 30.0):
            u = np.array([r['u'][0], gap0, Lo0, 0.0])
            for it in range(2):
                q = minimize(cost, u, args=(cfg,), method="Nelder-Mead", options=dict(maxiter=300, xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
            if best is None or q.fun < best[0]: best = (q.fun, u)
    ts, gap, Lo, dz = best[1]; S, zl = O.build(cfg, ts, gap); zo = O.para_focus(S, zl, Lo)+dz
    rms, c, m, fr = O.metrics(cfg, ts, gap, Lo, zo, n=20)
    out.append(dict(cfg=cfg, cost=best[0], u=best[1].tolist(), rms_um=(rms*1e3).round(1).tolist(), m=m, vign_min=float(fr.min())))
    print(cfg, "cost", round(best[0],1), "ts,gap,Lo,dz", np.round(best[1],1), "rms", (rms*1e3).round(1).tolist(), "m", round(m,3), "xrange", round(c[:,0].min(),2), round(c[:,0].max(),2), "vig", round(fr.min(),2), flush=True)
json.dump(out, open('../results/stock_refined.json', 'w'), indent=1)
