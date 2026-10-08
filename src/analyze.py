"""Full analysis of the optimised two-doublet channel -> results/*.png, results/summary.json"""
import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar
from opt2 import *
from eye import glints
d = json.load(open('../results/two_doublet.json')); v = np.array(d['v']); g = d['glass']
x = v[:8]; Lo, zo = v[8], v[9]
F9 = fields(n=3, ex=EX, ey=EY, xc=XC)
OUT = {}

def spots(x, Lo, zo, F=F9, wls=WLS, n=24):
    return [run(x, g, Lo, zo, w, F, n=n) for w in wls]
def rms_of(sp, i):
    pts = np.vstack([sp[k][i] for k in range(len(sp))]); c = sp[1][i].mean(0)
    return np.sqrt(((pts-c)**2).sum(1).mean()), c
# ---- nominal numbers
sp = spots(x, Lo, zo)
R = np.array([rms_of(sp, i)[0] for i in range(9)]); C = np.array([rms_of(sp, i)[1] for i in range(9)])
m = abs((C[3,0]-C[5,0])/EX + (C[1,1]-C[7,1])/EY)/2
OUT['rms_um'] = (R*1e3).reshape(3,3).round(2).tolist(); OUT['m'] = m
OUT['image_x_range_mm'] = [float(C[:,0].min()), float(C[:,0].max())]; OUT['image_y_range_mm'] = [float(C[:,1].min()), float(C[:,1].max())]
# distortion: deviation from linear map fitted on the 9 chief points
A = np.column_stack([np.ones(9), F9[:,0], F9[:,1]])
res = max(np.abs(C[:,k] - A@np.linalg.lstsq(A, C[:,k], rcond=None)[0]).max() for k in (0,1))
OUT['max_nonlinearity_um'] = res*1e3
# ---- spot diagram figure
fig, ax = plt.subplots(3, 3, figsize=(8, 8))
for i in range(9):
    a = ax[i//3, i % 3]
    for k, col in enumerate(['tab:blue', 'tab:green', 'tab:red']):
        p = (sp[k][i]-C[i])*1e3; a.plot(p[:, 0], p[:, 1], '.', ms=2, color=col)
    a.set_xlim(-30, 30); a.set_ylim(-30, 30); a.set_aspect('equal'); a.add_patch(plt.Rectangle((-5,-5),10,10,fill=False,ls='--',color='k',lw=.7))
    a.set_title(f"eye ({F9[i,0]-XC:+.1f},{F9[i,1]:+.1f}) mm  rms {R[i]*1e3:.1f} µm", fontsize=7); a.tick_params(labelsize=6)
fig.suptitle("Spot diagrams (µm), dashed = 10 µm pixel; 840/850/860 nm"); fig.tight_layout(); fig.savefig('../results/spots.png', dpi=130); plt.close()
# ---- MTF (geometric LSF x diffraction) at 25 lp/mm and curves
lam = 0.85e-3
# image-space NA from the on-axis-of-eye marginal rays
S_, zl = build(x, g)
P_, D_ = rays_from(F9[4], Lo, XC, 3.125, 14)
Pn, Dn, al = trace(to_plane(P_, D_, 0.0), D_, S_, 0.85)
ang = np.arccos(np.clip(Dn[al][:,2], -1, 1)); NA = np.sin(ang.max()-0) if False else np.sin((np.ptp(np.arctan2(Dn[al][:,0], Dn[al][:,2])))/2)
fc = 2*NA/lam; OUT['image_NA'] = float(NA); OUT['working_fnum'] = float(1/(2*NA)); OUT['diff_cutoff_lpmm'] = float(fc)
def dmtf(f): 
    r = np.clip(f/fc, 0, 1); return 2/np.pi*(np.arccos(r) - r*np.sqrt(1-r*r))
fr = np.linspace(0, 50, 101)
def gmtf(pts, c):
    p = (pts - c)  # mm
    out = []
    for ax_ in (0, 1):
        q = p[:, ax_]; out.append(np.abs(np.exp(-2j*np.pi*np.outer(fr, q)).mean(1)))
    return out
fig, ax = plt.subplots(1, 2, figsize=(10, 4)); mt = {}
for i in range(9):
    pts = np.vstack(sp); pts = np.vstack([sp[k][i] for k in range(3)]); c = sp[1][i].mean(0)
    gx, gy = gmtf(pts, c); mt[i] = (gx*dmtf(fr), gy*dmtf(fr))
    ax[0].plot(fr, mt[i][0], lw=1); ax[1].plot(fr, mt[i][1], lw=1)
for a, t in zip(ax, ("sagittal (x)", "tangential (y)")):
    a.plot(fr, dmtf(fr), 'k--', label='diffraction'); a.axvline(25, color='gray', ls=':'); a.axvline(50, color='gray', ls=':'); a.set_title(t); a.set_xlabel('lp/mm'); a.set_ylim(0, 1)
ax[0].legend(); fig.suptitle("MTF (geometric x diffraction, 840-860 nm), 9 fields; Nyquist = 50 lp/mm"); fig.tight_layout(); fig.savefig('../results/mtf.png', dpi=130); plt.close()
k25 = 50  # index of 25 lp/mm
OUT['mtf25_min'] = float(min(min(a[k25], b[k25]) for a, b in mt.values())); OUT['mtf25_diff'] = float(dmtf(25.0))
# ---- depth of field at fixed focus
dof = []
for dz in (-2, -1, 0, 1, 2):
    s2 = spots(x, Lo+dz, zo, F=F9[[4, 0, 2]], n=14)
    r = [np.sqrt(((np.vstack([s2[k][i] for k in range(3)]) - s2[1][i].mean(0))**2).sum(1).mean())*1e3 for i in range(3)]
    dof.append((dz, round(r[0], 1), round(max(r), 1)))
OUT['dof_rms_um(dz,centre,worst3)'] = dof
# ---- IPD sweep: path +-5 mm, refocus with sensor shift
ipd = []
for dz in (-5, 0, 5):
    f = lambda z: np.mean([rms_of(spots(x, Lo+dz, z, F=F9[[4, 0, 2, 6, 8]], n=12), i)[0] for i in range(5)])
    r = minimize_scalar(f, bounds=(zo-4, zo+4), method='bounded', options=dict(xatol=1e-3))
    s2 = spots(x, Lo+dz, r.x, F=F9, n=12); C2 = np.array([rms_of(s2, i)[1] for i in range(9)])
    m2 = abs((C2[3,0]-C2[5,0])/EX + (C2[1,1]-C2[7,1])/EY)/2
    ipd.append(dict(dLo=dz, refocus_mm=float(r.x-zo), rms_um=float(r.fun*1e3), m=float(m2), inner_edge_mm=float(C2[:,0].min()), outer_edge_mm=float(C2[:,0].max())))
OUT['ipd_sweep'] = ipd
# ---- folded geometry
IPD, d_h, s_o = 63.0, 6.5*2, 30.0
OUT['fold'] = dict(Lo=float(Lo), eye_to_M1=s_o, M1_to_V=IPD/2-d_h/2, V_to_stop=float(Lo)-s_o-(IPD/2-d_h/2),
                   M1_to_V_range=[54/2-d_h/2, 74/2-d_h/2])
# ---- Purkinje on sensor: P1-P4 vector -> sensor, vs gaze
sl = []
for th in range(-15, 16, 5):
    gy_ = glints(0, th); gx_ = glints(th, 0)
    sl.append(dict(theta=th, dx_h=float(((gy_[1][0]-gy_[4][0])[0])*m*-1), dy_v=float(((gx_[1][0]-gx_[4][0])[1])*m)))
OUT['P1P4_on_sensor_mm'] = sl
# ---- prescription
OUT['prescription'] = dict(glass=g, R=x[:6].tolist(), t_crown=T1, t_flint=T2, stop_to_L1=float(x[6]), gap=float(x[7]), Lo=float(Lo), last_to_filter_then_sensor_offset=float(zo), filter_mm=FILT_T, cover_mm=COVER_T)
json.dump(OUT, open('../results/summary.json', 'w'), indent=1, default=float)
print(json.dumps(OUT, indent=1, default=float))
