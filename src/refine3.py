import json, numpy as np
from scipy.optimize import minimize
import search3 as S, stock_final as SF
from channel import fields
from raytrace import trace, index
D = 12.0; HALF = 6.5
SF.build = S.build_multi; SF.SR = D/2; SF.XC = -HALF
F = fields(n=3, ex=11.6, ey=15.2, xc=-HALF)
rows = sorted(json.load(open('../results/search3_D12.json')), key=lambda r: r['cost'])[:4]
def cost(u, ng, n):
    ts, b = u[0], u[-1]; gaps = u[1:1+ng]; Lo = u[1+ng]
    if not (0.3 <= ts <= 12 and np.all(gaps >= 0.3) and np.all(gaps <= 140) and 150 <= Lo <= 215 and 8 <= b <= 170 and 195 <= Lo + SF.FILT_T + ts <= 205): return 1e6
    try: r = SF.metrics((ts, gaps, b), Lo, F=F, n=n)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr, _ = r
    return (rms*1e3).mean() + 0.3*rms.max()*1e3 + 1500*max(0, abs(m-0.56)-0.03) + 150*(1-fr).max() + 300*max(0, 0.3-c[:, 0].min()) + 300*max(0, c[:, 0].max()-9.3)
out = []
for r in rows:
    SF.CFG = [tuple(c) for c in r['cfg']]; ng = len(SF.CFG)-1; u = np.array(r['u']); best = None
    for trial in range(2):
        for it in range(3):
            q = minimize(cost, u, args=(ng, 12), method="Nelder-Mead", options=dict(maxiter=500, xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
        if best is None or q.fun < best[0]: best = (q.fun, u.copy())
        u = u + np.r_[0.3, np.full(ng, 2.0), 0, 5.0]*np.random.default_rng(trial).normal(size=ng+3)*0.5
    u = best[1]; ts, b = u[0], u[-1]; gaps = u[1:1+ng]; Lo = u[1+ng]
    rms, c, m, fr, sp = SF.metrics((ts, gaps, b), Lo, F=F, n=20)
    Ssys, zs = S.build_multi(ts, gaps, b); P, Dr = SF.rays_from(F[4], Lo, SF.XC, SF.SR, 14); Pc, Dc = SF.to_plane(P, Dr, 0.), Dr; n = 1.0
    for s in Ssys:
        Pc, Dc, a = trace(Pc, Dc, [s], 0.85, n)
        if s.kind != "stop": n = index(s.after, 0.85)
    NA = np.sin(np.ptp(np.arctan2(Dc[a][:, 0], Dc[a][:, 2]))/2); fc = 2*NA/0.85e-3; rr = 25/fc; dm = 2/np.pi*(np.arccos(rr)-rr*np.sqrt(1-rr*rr))
    o = np.array([[abs(np.exp(-2j*np.pi*25*(np.vstack([sp[k][i] for k in range(3)])-sp[1][i].mean(0))[:, ax]).mean())*dm for ax in (0, 1)] for i in range(9)])
    res = dict(cfg=SF.CFG, u=u.tolist(), eye_to_lens=float(Lo+SF.FILT_T+ts), m=float(m), rms_um=(rms*1e3).tolist(), rms_mean=float(rms.mean()*1e3), rms_max=float(rms.max()*1e3), vig=float(fr.min()), xr=[float(c[:, 0].min()), float(c[:, 0].max())], mtf25_min=float(o.min()), mtf25_mean=float(o.mean()), fnum=float(1/(2*NA)), cost=float(best[0]))
    out.append(res); print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in res.items() if k != 'rms_um'}), flush=True)
json.dump(out, open('../results/search3_refined_D12.json', 'w'), indent=1)
