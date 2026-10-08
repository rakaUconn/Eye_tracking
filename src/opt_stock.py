import sys, json, itertools, numpy as np
from scipy.optimize import minimize
from raytrace import Surf, trace, to_plane
from channel import fields, rays_from, pupil, WLS, FILT_T, COVER_T
from stock import element
M_T = 0.55; EX, EY = 11.6, 15.2; XC = -6.5; STOP_R = 3.125
F9 = fields(n=3, ex=EX, ey=EY, xc=XC)

def build(cfg, ts, gap):
    S = []; z = ts; ztot = []
    for k, (name, flip) in enumerate(cfg):
        el, dia = element(name, flip)
        for R, t, med in el:
            S.append(Surf(z, R, med, ap=(0, 0, 0.45*dia))); z += t
        if k < len(cfg)-1: z += gap
    return S, z - 0.0
def plates(z0):
    return [Surf(z0, np.inf, "N-BK7"), Surf(z0+FILT_T, np.inf, "air"),
            Surf(z0+FILT_T+.5, np.inf, "N-BK7"), Surf(z0+FILT_T+.5+COVER_T, np.inf, "air")]
def para_focus(S, zl, Lo):
    # axial object at lens axis, two tiny rays -> axis crossing behind last surface (no stop)
    h = 0.2; P = np.array([[0, 0, -Lo], [0, 0, -Lo]], float)
    T = np.array([[h, 0, 0], [-h, 0, 0]], float); D = T - P; D /= np.linalg.norm(D, axis=1)[:, None]
    P0 = to_plane(P, D, 0.0); Pn, Dn, al = trace(P0, D, S, 0.85)
    Pn, Dn, al = trace(Pn, Dn, plates(zl), 0.85)
    zb = zl + FILT_T + .5 + COVER_T
    t = -Pn[0, 0]/Dn[0, 0] if False else (Pn[1, 0]-Pn[0, 0]) / (Dn[0, 0]-Dn[1, 0])
    return Pn[0, 2] + t*Dn[0, 2] - zb
def run(S, zl, Lo, zoff, wl, F, n=10):
    out = []; frac = []
    N0 = len(pupil(XC, STOP_R, n)[0])
    for f in F:
        P, D = rays_from(f, Lo, XC, STOP_R, n); P0 = to_plane(P, D, 0.0)
        Pn, Dn, a = trace(P0, D, S, wl); Pn, Dn, a2 = trace(Pn, Dn, plates(zl), wl)
        Q = to_plane(Pn, Dn, zl + FILT_T + .5 + COVER_T + zoff); ok = a & a2
        out.append(Q[ok][:, :2]); frac.append(ok.sum()/N0)
    return out, frac
def metrics(cfg, ts, gap, Lo, zoff, F=F9, wls=WLS, n=10):
    S, zl = build(cfg, ts, gap)
    res = [run(S, zl, Lo, zoff, w, F, n) for w in wls]
    sp = [r[0] for r in res]; fr = np.min([r[1] for r in res], axis=0)
    rms = []; c = []
    for i in range(len(F)):
        pts = [sp[k][i] for k in range(len(wls))]
        if any(len(a) < 6 for a in pts): return None
        cc = pts[len(wls)//2].mean(0); c.append(cc); a = np.vstack(pts)-cc; rms.append(np.sqrt((a**2).sum(1).mean()))
    c = np.array(c)
    m = abs((c[3, 0]-c[5, 0])/EX + (c[1, 1]-c[7, 1])/EY)/2 if len(F) == 9 else 0
    return np.array(rms), c, m, fr
def cost(u, cfg):
    ts, gap, Lo, dz = u
    if not (0 <= ts <= 40 and 0 <= gap <= 120 and 140 <= Lo <= 160 and abs(dz) < 6): return 1e6
    try:
        S, zl = build(cfg, ts, gap); zo = para_focus(S, zl, Lo) + dz
        r = metrics(cfg, ts, gap, Lo, zo)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m, fr = r
    return (rms*1e3).mean() + 0.3*rms.max()*1e3 + 2000*abs(m-M_T) + 150*(1-fr).max()
if __name__ == "__main__":
    names = ["AC254-050", "AC254-075-B", "AC254-150", "AC508-150-B", "LBF254-050", "LB1471", "LA1131", "LE1234"]
    singles = [[(n, f)] for n in names for f in (0, 1)]
    pairs = [[(a, fa), (b, fb)] for a in names for b in names for fa in (0, 1) for fb in (0, 1)]
    part = int(sys.argv[1]); cfgs = (singles + pairs)[part::4]
    res = []
    for cfg in cfgs:
        best = None
        for gap0 in ((0.0,) if len(cfg) == 1 else (3.0, 20.0, 50.0)):
            u = np.array([2.0, gap0, 149.4, 0.0])
            for it in range(2):
                r = minimize(cost, u, args=(cfg,), method="Nelder-Mead", options=dict(maxiter=250, xatol=1e-3, fatol=1e-3, adaptive=True)); u = r.x
            if best is None or r.fun < best[0]: best = (r.fun, u.tolist())
        res.append(dict(cfg=cfg, cost=best[0], u=best[1])); print(cfg, round(best[0], 1), np.round(best[1], 1), flush=True)
        json.dump(res, open(f"../results/stock_search_{part}.json", "w"))
