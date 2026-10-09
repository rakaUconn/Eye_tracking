import json, numpy as np
from scipy.optimize import minimize
import stock_final as SF
from channel import fields
from raytrace import trace, index
SF.SR = 6.0; SF.XC = -6.5
F = fields(n=3, ex=11.6, ey=15.2, xc=-6.5)
def cost(u, n=9, mt=0.5):
    ts, gap, Lo, b = u
    if not (0.3 <= ts <= 12 and 100 <= gap <= 330 and 140 <= Lo <= 215 and 20 <= b <= 170 and 150 <= Lo + SF.FILT_T + ts <= 200): return 1e6
    try: r = SF.metrics((ts, gap, b), Lo, F=F, n=n)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr, _ = r
    return (rms*1e3).mean() + 0.3*rms.max()*1e3 + 1500*max(0, abs(m-mt)-0.02) + 150*(1-fr).max() + 300*max(0, 0.3-c[:, 0].min()) + 300*max(0, c[:, 0].max()-9.3)
out = []
for f1 in (0, 1):
    for f2 in (0, 1):
        SF.CFG = [("AC254-150", f1), ("AC254-075-B", f2)]; best = None
        for Lo0, gap0, b0 in ((150., 217., 70.), (150., 120., 100.), (170., 150., 90.)):
            u = np.array([1.0, gap0, Lo0, b0])
            for it in range(3):
                q = minimize(cost, u, method="Nelder-Mead", options=dict(maxiter=300, xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
            if best is None or q.fun < best[0]: best = (q.fun, u.copy())
        ts, gap, Lo, b = best[1]; rms, c, m, fr, sp = SF.metrics((ts, gap, b), Lo, F=F, n=20)
        print(SF.CFG, "cost", round(best[0], 1), "ts,gap,Lo,b", np.round(best[1], 1), "eye->lens1", round(Lo+SF.FILT_T+ts, 1), "rms", (rms*1e3).round(1).tolist(), "m", round(m, 3), "xr", c[:, 0].min().round(2), c[:, 0].max().round(2), "vig", fr.min().round(2), flush=True)
        out.append(dict(cfg=SF.CFG, u=best[1].tolist(), cost=best[0], rms_um=(rms*1e3).tolist(), m=m, vig=float(fr.min()), xr=[float(c[:, 0].min()), float(c[:, 0].max())]))
json.dump(out, open('../results/relay_front_150_75.json', 'w'), indent=1)
