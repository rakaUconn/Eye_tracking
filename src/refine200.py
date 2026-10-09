import json, glob, numpy as np
from scipy.optimize import minimize
import stock_final as SF
rows = []
for f in glob.glob('../results/stock200_[0-3].json'): rows += json.load(open(f))
rows = sorted(rows, key=lambda r: r['cost'])[:5]
def cost(u, n):
    ts, gap, Lo, b = u
    if not (0.3 <= ts <= 10 and 0.3 <= gap <= 60 and 195 <= Lo <= 205 and 30 <= b <= 160): return 1e6
    try: r = SF.metrics((ts, gap, b), Lo, n=n)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr, _ = r
    return (rms*1e3).mean()+0.3*rms.max()*1e3+1500*abs(m-0.55)+150*(1-fr).max()
def mtf25(par, Lo):
    rms, c, m, fr, sp = SF.metrics(par, Lo, n=24)
    from raytrace import trace, index
    S, zs = SF.build(*par); P, D = SF.rays_from(SF.F9[4], Lo, SF.XC, SF.SR, 14); Pc, Dc = SF.to_plane(P, D, 0.), D; n = 1.0
    for s in S:
        Pc, Dc, a = trace(Pc, Dc, [s], 0.85, n)
        if s.kind != "stop": n = index(s.after, 0.85)
    NA = np.sin(np.ptp(np.arctan2(Dc[a][:, 0], Dc[a][:, 2]))/2); fc = 2*NA/0.85e-3; r = 25/fc; dm = 2/np.pi*(np.arccos(r)-r*np.sqrt(1-r*r))
    o = []
    for i in range(9):
        p = np.vstack([sp[k][i] for k in range(3)]) - sp[1][i].mean(0)
        o.append([abs(np.exp(-2j*np.pi*25*p[:, ax]).mean())*dm for ax in (0, 1)])
    return np.array(o), 1/(2*NA), dm, rms, c, m, fr
out = []
for r in rows:
    SF.CFG = [tuple(c) for c in r['cfg']]; u = np.array(r['u'])
    for it in range(3):
        q = minimize(cost, u, args=(14,), method="Nelder-Mead", options=dict(maxiter=250, xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
    ts, gap, Lo, b = u; o, fn, dm, rms, c, m, fr = mtf25((ts, gap, b), Lo)
    print(SF.CFG, "u", np.round(u, 2), "rms", (rms*1e3).round(1).tolist(), "m", round(m, 3), "xr", c[:, 0].min().round(2), c[:, 0].max().round(2), "MTF25 min/mean", o.min().round(2), o.mean().round(2), "f/#", round(fn, 1), flush=True)
    out.append(dict(cfg=SF.CFG, u=u.tolist(), rms_um=(rms*1e3).tolist(), m=m, mtf25_min=float(o.min()), mtf25_mean=float(o.mean()), fnum=fn, xr=[float(c[:,0].min()), float(c[:,0].max())], vign=float(fr.min())))
json.dump(out, open('../results/stock200_refined.json', 'w'), indent=1)
