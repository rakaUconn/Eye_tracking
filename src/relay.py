"""Relay design from the user's sketch: eye plane -> lens1 (AC254-150-B) -> crossing -> lens2 (AC254-075-B) -> two-hole stop plate -> sensor.
Magnification f2/f1 = 0.5.  Rays are launched over a wide cone and clipped by the stop (no ray aiming)."""
import json, sys, numpy as np
from scipy.optimize import minimize
from raytrace import Surf, trace, to_plane, index
from stock import element
from channel import fields
FILT_T, COVER_T, COVER_GAP = 3.0, 1.0, 0.5
WLS = (0.84, 0.85, 0.86); XC = -6.5
def build(par, cfg, Db, xs):
    """par = (d0 unused, gap12, sbd, b); surfaces start at z=0 (lens1 front vertex). Stop plate (with filter) sbd after lens 2; cover glass b after the plate."""
    gap12, sbd, b = par
    S = []; z = 0.0; zs = []
    for k, (name, flip) in enumerate(cfg):
        el, dia = element(name, flip)
        for R, t, med in el:
            S.append(Surf(z, R, med, ap=(0, 0, 0.45*dia))); z += t
        if k < len(cfg)-1: z += gap12
    zst = z + sbd
    S.append(Surf(zst, kind="stop", ap=(xs, 0, Db/2)))            # two-hole plate (left channel hole shown)
    S += [Surf(zst, np.inf, "N-BK7"), Surf(zst+FILT_T, np.inf, "air")]       # band-pass filter on the plate
    zc = zst + FILT_T + b
    S += [Surf(zc, np.inf, "N-BK7"), Surf(zc+COVER_T, np.inf, "air")]
    return S, zc + COVER_T + COVER_GAP, zst
def launch(f, d0, n=34, RL=9.0, xl=XC):
    g = np.linspace(-RL, RL, n); X, Y = np.meshgrid(g, g); m = X**2+Y**2 <= RL**2
    T = np.column_stack([xl + X[m], Y[m], np.zeros(m.sum())]); P = np.tile([f[0], f[1], -d0], (len(T), 1))
    D = T - P; return P, D/np.linalg.norm(D, axis=1)[:, None], T
def run(S, zs, f, d0, wl, n=34):
    P, D, T = launch(f, d0, n); n_med = 1.0; Pc, Dc = P.copy(), D.copy(); alive = np.ones(len(P), bool)
    for s in S:
        Pc, Dc, al = trace(Pc, Dc, [s], wl, n_med); alive &= al
        if s.kind != "stop": n_med = index(s.after, wl)
    Q = to_plane(Pc, Dc, zs); return Q[alive][:, :2], alive.sum()
def metrics(par, d0, cfg, Db, xs, F, wls=WLS, n=34):
    S, zs, zst = build(par, cfg, Db, xs); sp = []; cnt = []
    for w in wls:
        r = [run(S, zs, f, d0, w, n) for f in F]; sp.append([x[0] for x in r]); cnt.append([x[1] for x in r])
    cnt = np.min(cnt, axis=0); rms = []; c = []
    for i in range(len(F)):
        if any(len(sp[k][i]) < 8 for k in range(len(wls))): return None
        cc = sp[1][i].mean(0); c.append(cc); a = np.vstack([sp[k][i] for k in range(len(wls))]) - cc; rms.append(np.sqrt((a**2).sum(1).mean()))
    c = np.array(c); m = abs((c[3, 0]-c[5, 0])/11.6 + (c[1, 1]-c[7, 1])/15.2)/2
    return np.array(rms), c, m, cnt/cnt.max(), sp
F9 = fields(n=3, ex=11.6, ey=15.2, xc=XC)
def cost(u, cfg, Db, xs):
    d0, gap12, sbd, b = u
    if not (150 <= d0 <= 200 and 100 <= gap12 <= 300 and 3 <= sbd <= 80 and 20 <= b <= 140): return 1e6
    try: r = metrics((gap12, sbd, b), d0, cfg, Db, xs, F9, n=24)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr, _ = r
    return (rms*1e3).mean() + 0.3*rms.max()*1e3 + 1500*max(0, abs(m-0.5)-0.02) + 150*(1-fr).max() + 300*max(0, 0.3-c[:, 0].min()) + 300*max(0, c[:, 0].max()-9.3)
if __name__ == "__main__":
    Db = float(sys.argv[1]) if len(sys.argv) > 1 else 5.5; xs = 3.25
    res = []
    for f1 in (0, 1):
        for f2 in (0, 1):
            cfg = [("AC254-150", f1), ("AC254-075-B", f2)]; best = None
            for sbd0 in (10., 40.):
                u = np.array([150., 217., sbd0, 70.])
                for it in range(3):
                    q = minimize(cost, u, args=(cfg, Db, xs), method="Nelder-Mead", options=dict(maxiter=250, xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
                if best is None or q.fun < best[0]: best = (q.fun, u.copy())
            d0, gap12, sbd, b = best[1]
            rms, c, m, fr, sp = metrics((gap12, sbd, b), d0, cfg, Db, xs, F9, n=40)
            print(cfg, "cost", round(best[0], 1), "d0,gap,sbd,b", np.round(best[1], 1), "rms", (rms*1e3).round(1).tolist(), "m", round(m, 3), "xr", c[:, 0].min().round(2), c[:, 0].max().round(2), "vig", fr.min().round(2), flush=True)
            res.append(dict(cfg=cfg, u=best[1].tolist(), cost=best[0], rms_um=(rms*1e3).tolist(), m=m, vig=float(fr.min()), xr=[float(c[:, 0].min()), float(c[:, 0].max())], Db=Db))
    json.dump(res, open(f"../results/relay150_75_Db{Db}.json", "w"), indent=1)
