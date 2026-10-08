import numpy as np, json
from scipy.optimize import minimize
from channel import *
M_T = 0.55; EX, EY = 11.6, 15.2; XC = -6.5
F9 = fields(n=3, ex=EX, ey=EY, xc=XC)

def evaluate(p, Lo, zoff, wls=WLS, F=F9):
    allsp = [image_spots(p, Lo, zoff, wl=w, F=F, stop_x=XC) for w in wls]
    rms = []; cents = []
    for i in range(len(F)):
        pts = [allsp[k][i] for k in range(len(wls))]
        if any(len(a) < 20 for a in pts): return None
        c = pts[1].mean(0); cents.append(c)
        a = np.vstack(pts) - c
        rms.append(np.sqrt((a**2).sum(1).mean()))
    return np.array(rms), np.array(cents)

def mag(c):
    return abs((c[3,0]-c[5,0])/EX + (c[1,1]-c[7,1])/EY)/2

def cost(x, g1, g2):
    R1, R2, R3, ts, Lo, zoff = x
    p = dict(R1=R1, R2=R2, R3=R3, t1=8.0, t2=3.0, ts=ts, g1=g1, g2=g2)
    if not (0<=ts<=25 and 135<=Lo<=150 and 40<=zoff<=90 and min(abs(R1),abs(R2),abs(R3))>=18): return 1e6
    try: r = evaluate(p, Lo, zoff)
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c = r
    return (rms*1e3).mean() + 0.3*rms.max()*1e3 + 2000*abs(mag(c)-M_T)

if __name__ == "__main__":
    res = {}
    for (g1, g2) in [("N-BK7","F2"), ("N-BK7","N-SF5"), ("N-BK7","N-SF6"), ("F2","N-BK7"), ("N-SF6","N-BK7")]:
        best = None
        for sc in (1.0, 1.2):
            x0 = [33*sc, -24*sc, -130*sc, 6.0, 141.0, 62.0] if g1 == "N-BK7" else [-130*sc, 24*sc, 33*sc, 6.0, 141.0, 62.0]
            for it in range(3):
                r = minimize(cost, x0, args=(g1, g2), method="Nelder-Mead", options=dict(maxiter=250, xatol=1e-3, fatol=1e-4))
                x0 = r.x
            if best is None or r.fun < best.fun: best = r
        print(g1, g2, round(best.fun, 2), np.round(best.x, 3), flush=True)
        res[f"{g1}/{g2}"] = dict(cost=best.fun, x=list(best.x))
    json.dump(res, open("../results/doublet_opt.json", "w"), indent=1)
