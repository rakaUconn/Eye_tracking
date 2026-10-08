"""Final stock-lens design: AC254-150-B (rev.) + AC254-075-B, filter at the stop, cover glass on the sensor."""
import json, numpy as np
from scipy.optimize import minimize
from raytrace import Surf, trace, to_plane, index
from channel import fields, rays_from, pupil, WLS
from stock import element
XC, SR = -6.5, 3.125; EX, EY = 11.6, 15.2; M_T = 0.55
FILT_T, FILT_G = 3.0, "N-BK7"     # FBH850-10 stand-in (check vendor thickness/substrate)
COVER_T, COVER_GAP = 1.0, 0.5     # sensor cover glass + air gap to die (placeholders)
CFG = [("AC254-150", 1), ("AC254-075-B", 0)]
F9 = fields(n=3, ex=EX, ey=EY, xc=XC)

def build(ts, gap, b):
    """returns surface list (stop first) and z of cover front/back/sensor. z=0 is the stop / filter front."""
    S = [Surf(0.0, kind="stop", ap=(XC, 0, SR)), Surf(0.0, np.inf, FILT_G), Surf(FILT_T, np.inf, "air")]
    z = FILT_T + ts
    for k, (name, flip) in enumerate(CFG):
        el, dia = element(name, flip)
        for R, t, med in el:
            S.append(Surf(z, R, med, ap=(0, 0, 0.45*dia))); z += t
        if k < len(CFG)-1: z += gap
    zc = z + b
    S += [Surf(zc, np.inf, "N-BK7"), Surf(zc+COVER_T, np.inf, "air")]
    return S, zc+COVER_T+COVER_GAP          # sensor plane z

def trace_points(S, zs, P0, D, wl):
    """full trace returning image-plane XY of surviving rays"""
    n = 1.0
    P, Dd = P0, D
    alive = np.ones(len(P0), bool)
    for s in S:
        P, Dd, al = trace(P, Dd, [s], wl, n); alive &= al
        if s.kind != "stop": n = index(s.after, wl)
    Q = to_plane(P, Dd, zs)
    return Q, alive

def spots(par, wl, F, Lo, n=14, extra_dz=0.0):
    ts, gap, b = par
    S, zs = build(ts, gap, b); out = []; frac = []
    N0 = len(pupil(XC, SR, n)[0])
    for f in F:
        P, D = rays_from(f, Lo, XC, SR, n); P0 = to_plane(P, D, 0.0)
        Q, al = trace_points(S, zs, P0, D, wl)
        out.append(Q[al][:, :2]); frac.append(al.sum()/N0)
    return out, np.array(frac)

def metrics(par, Lo, F=F9, wls=WLS, n=10):
    res = [spots(par, w, F, Lo, n) for w in wls]; sp = [r[0] for r in res]; fr = np.min([r[1] for r in res], axis=0)
    rms = []; c = []
    for i in range(len(F)):
        pts = [sp[k][i] for k in range(len(wls))]
        if any(len(a) < 6 for a in pts): return None
        cc = pts[1].mean(0); c.append(cc); a = np.vstack(pts)-cc; rms.append(np.sqrt((a**2).sum(1).mean()))
    c = np.array(c); m = abs((c[3, 0]-c[5, 0])/EX + (c[1, 1]-c[7, 1])/EY)/2
    return np.array(rms), c, m, fr, sp

def cost(u):
    ts, gap, Lo, b = u
    if not (0 <= ts <= 10 and 0 <= gap <= 30 and 120 <= Lo <= 175 and 40 <= b <= 100): return 1e6
    try: r = metrics((ts, gap, b), Lo)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr, _ = r
    return (rms*1e3).mean()+0.3*rms.max()*1e3+2000*abs(m-M_T)+150*(1-fr).max()

if __name__ == "__main__":
    best = None
    for Lo0 in (137.3, 149.4):
        for b0 in (66., 72., 78.):
            u = np.array([0.5, 0.1, Lo0, b0])
            for it in range(3):
                q = minimize(cost, u, method="Nelder-Mead", options=dict(maxiter=300, xatol=1e-3, fatol=1e-3, adaptive=True)); u = q.x
            print(Lo0, b0, round(q.fun, 1), np.round(u, 2), flush=True)
            if best is None or q.fun < best[0]: best = (q.fun, u)
    ts, gap, Lo, b = best[1]
    rms, c, m, fr, sp = metrics((ts, gap, b), Lo, n=20)
    print("FINAL", np.round(best[1], 3), "rms", (rms*1e3).round(1).tolist(), "m", round(m, 4), "x", c[:, 0].min().round(2), c[:, 0].max().round(2), "vig", fr.min())
    json.dump(dict(ts=ts, gap=gap, Lo=Lo, b=b, rms_um=(rms*1e3).tolist(), m=m, cost=best[0],
                   filt=(FILT_T, FILT_G), cover=(COVER_T, COVER_GAP)), open("../results/stock_final.json", "w"), indent=1)
