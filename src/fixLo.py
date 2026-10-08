import json, numpy as np, opt_stock as O
from scipy.optimize import minimize
LO = 149.4
def cost(u, cfg):
    ts, gap, dz = u
    if not (0 <= ts <= 40 and 0 <= gap <= 120 and abs(dz) < 8): return 1e6
    try:
        S, zl = O.build(cfg, ts, gap); r = O.metrics(cfg, ts, gap, LO, O.para_focus(S, zl, LO)+dz)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr = r
    return (rms*1e3).mean()+0.3*rms.max()*1e3+2000*abs(m-O.M_T)+150*(1-fr).max()
cfgs = [[('AC254-150',1),('AC254-075-B',0)], [('AC254-150',0),('AC254-075-B',0)], [('AC508-150-B',0),('AC254-075-B',0)], [('AC254-150',1),('AC254-075-B',1)], [('AC508-150-B',1),('AC254-075-B',0)]]
for cfg in cfgs:
    best = None
    for gap0 in (0., 10., 40.):
        u = np.array([0., gap0, 0.])
        for it in range(2):
            q = minimize(cost, u, args=(cfg,), method="Nelder-Mead", options=dict(maxiter=250, xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
        if best is None or q.fun < best[0]: best = (q.fun, u)
    ts, gap, dz = best[1]; S, zl = O.build(cfg, ts, gap); zo = O.para_focus(S, zl, LO)+dz
    rms, c, m, fr = O.metrics(cfg, ts, gap, LO, zo, n=20)
    print(cfg, "cost", round(best[0],1), "ts,gap,dz", np.round(best[1],2), "rms", (rms*1e3).round(1).tolist(), "m", round(m,3), "xr", round(c[:,0].min(),2), round(c[:,0].max(),2), flush=True)
