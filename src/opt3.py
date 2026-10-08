"""Re-optimise the two-doublet channel with a fixed eye->stop distance Lo (argv[1])."""
import sys, json, numpy as np
from scipy.optimize import minimize
from opt2 import *
Lo0 = float(sys.argv[1])
d = json.load(open('../results/two_doublet.json')); v0 = np.array(d['v']); g = tuple(d['glass'])
s = Lo0/v0[8]
v = np.r_[v0[:6]*s, v0[6], v0[7]*s, v0[9]*s]       # radii, ts, gap, zoff scaled; Lo fixed
def cost3(u):
    full = np.r_[u[:8], Lo0, u[8]]
    x = full[:8]
    if not(0<=x[6]<=25 and 0<=x[7]<=40 and 20<=full[9]<=130 and min(abs(x[:6]))>=20): return 1e6
    try: r = metrics(x, g, Lo0, full[9])
    except Exception: return 1e6
    if r is None: return 1e6
    rms, c, m = r
    return (rms*1e3).mean() + 0.3*rms.max()*1e3 + 2000*abs(m-M_T)
for it in range(7):
    r = minimize(cost3, v, method="Nelder-Mead", options=dict(maxiter=700, xatol=1e-3, fatol=1e-4, adaptive=True)); v = r.x
    print(Lo0, it, round(r.fun, 2), flush=True)
full = np.r_[v[:8], Lo0, v[8]]
json.dump(dict(glass=g, v=list(full), cost=r.fun), open(f"../results/two_doublet_Lo{int(Lo0)}.json", "w"), indent=1)
F9 = fields(n=3, ex=EX, ey=EY, xc=XC)
rms, c, m = metrics(full[:8], g, Lo0, full[9], F=F9, n=16)
print("FINAL", Lo0, "rms um", np.round(rms*1e3, 1).tolist(), "m", round(m, 3), "x range", round(c[:,0].min(),2), round(c[:,0].max(),2), "R", np.round(full[:6],1).tolist(), "ts,gap", np.round(full[6:8],2).tolist(), "zoff", round(full[9],1))
