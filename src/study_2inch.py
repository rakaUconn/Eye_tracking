"""Stop-diameter study: 1-inch vs 2-inch AC doublet pairs at eye->first lens 195-205 mm."""
import sys, json, numpy as np
from multiprocessing import Pool
from scipy.optimize import minimize
import stock_final as SF
from channel import fields
from raytrace import trace, index
CFGS = {"AC254-150 x2 (1 in)": [("AC254-150", 0), ("AC254-150", 0)], "AC508-150-B x2 (2 in)": [("AC508-150-B", 0), ("AC508-150-B", 0)]}
DS = [6.25, 9.0, 12.0, 15.0, 18.0]
def setup(D):
    half = max(6.5, D/2 + 0.3); SF.SR = D/2; SF.XC = -half
    return half, fields(n=3, ex=11.6, ey=15.2, xc=-half)
def cost(u, F, n):
    ts, gap, Lo, b = u
    if not (0.3 <= ts <= 12 and 0.3 <= gap <= 80 and 150 <= Lo <= 215 and 30 <= b <= 170 and 195 <= Lo + SF.FILT_T + ts <= 205): return 1e6
    try: r = SF.metrics((ts, gap, b), Lo, F=F, n=n)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr, _ = r
    return (rms*1e3).mean() + 0.3*rms.max()*1e3 + 1500*max(0, abs(m-0.56)-0.03) + 150*(1-fr).max() + 300*max(0, 0.3-c[:, 0].min()) + 300*max(0, c[:, 0].max()-9.3)
def job(args):
    name, D = args; cfg = CFGS[name]; SF.CFG = cfg; half, F = setup(D)
    best = None
    for gap0 in (0.5, 10.0):
        u = np.array([1.0, gap0, 196.0, 111.0])
        for it in range(3):
            q = minimize(cost, u, args=(F, 9), method="Nelder-Mead", options=dict(maxiter=220, xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
        if best is None or q.fun < best[0]: best = (q.fun, u)
    ts, gap, Lo, b = best[1]
    rms, c, m, fr, sp = SF.metrics((ts, gap, b), Lo, F=F, n=20)
    S, zs = SF.build(ts, gap, b); P, Dr = SF.rays_from(F[4], Lo, SF.XC, SF.SR, 14); Pc, Dc = SF.to_plane(P, Dr, 0.), Dr; n = 1.0
    for s in S:
        Pc, Dc, a = trace(Pc, Dc, [s], 0.85, n)
        if s.kind != "stop": n = index(s.after, 0.85)
    NA = np.sin(np.ptp(np.arctan2(Dc[a][:, 0], Dc[a][:, 2]))/2); fc = 2*NA/0.85e-3; r = 25/fc; dm = 2/np.pi*(np.arccos(r)-r*np.sqrt(1-r*r))
    o = []
    for i in range(9):
        p = np.vstack([sp[k][i] for k in range(3)]) - sp[1][i].mean(0)
        o.append([abs(np.exp(-2j*np.pi*25*p[:, ax]).mean())*dm for ax in (0, 1)])
    o = np.array(o)
    res = dict(name=name, D=D, half=half, u=[float(x) for x in best[1]], eye_to_lens=float(Lo + SF.FILT_T + ts), m=float(m), rms_um=(rms*1e3).tolist(),
               rms_max=float(rms.max()*1e3), rms_mean=float(rms.mean()*1e3), vig_min=float(fr.min()), x_range=[float(c[:, 0].min()), float(c[:, 0].max())],
               mtf25_min=float(o.min()), mtf25_mean=float(o.mean()), fnum=float(1/(2*NA)), light_vs_6p25=float((D/6.25)**2*fr.min()), cost=float(best[0]))
    print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in res.items() if k != 'rms_um'}), flush=True)
    return res
if __name__ == "__main__":
    jobs = [(n, D) for n in CFGS for D in DS]
    with Pool(4) as p: out = p.map(job, jobs)
    json.dump(out, open("../results/study_2inch.json", "w"), indent=1)
