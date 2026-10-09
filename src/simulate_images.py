"""Model-eye image simulation + analysis for the stock-lens objective (AC254-150 rev. + AC254-075-B).
Navarro eye -> P1/P4 glint positions (eye.py) -> ray-traced PSFs through the stock objective -> 1920x1080 frame
(10 um px, shot+read noise, 10-bit) -> glint detection/centroiding -> P1-P4 gaze mapping -> accuracy/precision."""
import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, label, center_of_mass, median_filter
from eye import glints
import stock_final as SF
from channel import rays_from

import os
DESIGN = os.environ.get('DESIGN', 'stock_final'); SUF = '' if DESIGN == 'stock_final' else '_' + DESIGN
P = json.load(open(f'../results/{DESIGN}.json'))
if 'cfg' in P: SF.CFG = [tuple(c) for c in P['cfg']]
PAR = (P['ts'], P['gap'], P['b']); LO = P['Lo']; M = P['m']
PX = 0.010; W, H = 1920, 1080; XC, SR = SF.XC, SF.SR
WL = 0.85; SUB = 5; SIG_DIFF_UM = 5.0                    # Gaussian stand-in for the Airy core at f/14
FWC, BITS, READ_E, P1_PEAK_E, P4_RATIO, BG_E = 15000., 10, 8.0, 9000., 0.012, 25.
BETA = {"L": 17.0, "R": -17.0}                          # source angle, mirrored for the second eye
S_STOCK, ZS = SF.build(*PAR)
# focal plane = mean P1/P4 depth at straight gaze
g0 = glints(0, 0); ZF = 0.5*(g0[1][0][2] + g0[4][0][2])

def gaze_glints(eye, tx, ty):
    g = glints(tx, ty, beta_deg=BETA[eye]); return g[1][0], g[4][0]          # lab xyz of P1, P4 virtual images

def psf_patch(xyz, eye):
    """ray-trace a point at lab position xyz through the channel -> (cx_px, cy_px, patch(sub-sampled), origin)"""
    px, py, pz = xyz
    s = -1.0 if eye == "R" else 1.0                         # right channel is the mirror image
    f = np.array([XC + s*px, py]); lo = LO + (pz - ZF)
    Pp, D = rays_from(f, lo, XC, SR, 60); P0 = SF.to_plane(Pp, D, 0.0)
    Q, al = SF.trace_points(S_STOCK, ZS, P0, D, WL); q = Q[al][:, :2]
    x = s*q[:, 0]; y = q[:, 1]                               # sensor mm (mirror back for R)
    return x, y

def render(glint_pairs, noise=False, rng=None):
    """glint_pairs: {eye: (P1xyz, P4xyz)} -> frame in electrons (float) and truth centroids (px)"""
    img = np.full((H, W), BG_E, float); truth = {}
    yy, xx = np.mgrid[0:H, 0:W]
    for eye, (p1, p4) in glint_pairs.items():
        truth[eye] = {}
        for name, p, amp in (("P1", p1, 1.0), ("P4", p4, P4_RATIO)):
            x, y = psf_patch(p, eye); cx = W/2 + x.mean()/PX; cy = H/2 - y.mean()/PX
            N = 41; c0, r0 = int(round(cx))-N//2, int(round(cy))-N//2
            xe = (np.arange(N*SUB+1)/SUB + c0 - 0.5 - W/2)*PX; ye = (H/2 - (np.arange(N*SUB+1)/SUB + r0 - 0.5))*PX
            hist, _, _ = np.histogram2d(y, x, bins=[ye[::-1], xe]); hist = hist[::-1]
            hist = gaussian_filter(hist, SIG_DIFF_UM/(PX*1000/SUB))
            patch = hist.reshape(N, SUB, N, SUB).sum((1, 3))
            patch *= amp*P1_PEAK_E/ (patch.max() if name == "P1" else PEAK_REF.get(eye, patch.max()))
            if name == "P1": PEAK_REF[eye] = hist.reshape(N, SUB, N, SUB).sum((1, 3)).max()
            img[r0:r0+N, c0:c0+N] += patch
            truth[eye][name] = (cx, cy)
    if noise:
        rng = rng or np.random.default_rng(1)
        img = rng.poisson(img).astype(float) + rng.normal(0, READ_E, img.shape)
    dn = np.clip(np.round(img/FWC*(2**BITS-1)), 0, 2**BITS-1)
    return dn, truth
PEAK_REF = {}

def detect(dn, eye):
    """find P1 (brightest) and P4 (second blob) in the half-frame of this eye; centroid with local background removal"""
    half = (slice(None), slice(W//2, W)) if eye == "L" else (slice(None), slice(0, W//2)); off = W//2 if eye == "L" else 0
    a = dn[half].astype(float); bg = median_filter(a[::4, ::4], size=15); bg = np.kron(bg, np.ones((4, 4)))[:a.shape[0], :a.shape[1]]
    s = a - bg; sig = 1.4826*np.median(np.abs(s - np.median(s)))+1e-9
    out = {}
    pk = np.unravel_index(np.argmax(s), s.shape); out["P1"] = refine(s, pk, off)
    m = s.copy(); r, c = pk; m[max(r-12, 0):r+13, max(c-12, 0):c+13] = 0           # mask P1 + its wings
    pk2 = np.unravel_index(np.argmax(m), m.shape)
    out["P4"] = refine(s, pk2, off) if m[pk2] > 6*sig else None
    return out
def refine(s, pk, off, hw=5):
    r, c = pk; sub = s[r-hw:r+hw+1, c-hw:c+hw+1].copy(); sub[sub < 0.15*sub.max()] = 0
    yy, xx = np.mgrid[-hw:hw+1, -hw:hw+1]; w = sub.sum()
    return (c + (xx*sub).sum()/w + off, r + (yy*sub).sum()/w)

def feature(det):                                   # P1-P4 vector in mm, eye-object space
    d = np.array(det["P1"]) - np.array(det["P4"]); return d*PX/M
def design_matrix(f, order=2):
    x, y = f[..., 0], f[..., 1]
    cols = [np.ones_like(x), x, y] + ([x*x, x*y, y*y] if order == 2 else [])
    return np.stack(cols, -1)

if __name__ == "__main__":
    rng = np.random.default_rng(7); res = {}
    # ---- 1. full frame at straight gaze and two other gaze states (both eyes, parallel gaze)
    states = {"straight (0°,0°)": (0, 0), "right 10°": (0, 10), "up 8°, left 12°": (8, -12)}
    fig = plt.figure(figsize=(14, 9)); gs = fig.add_gridspec(2, 3, height_ratios=[1.3, 1])
    axf = fig.add_subplot(gs[0, :]); frames = {}
    for k, (nm, (tx, ty)) in enumerate(states.items()):
        pairs = {e: gaze_glints(e, tx, ty) for e in ("L", "R")}
        dn, tr = render(pairs, noise=True, rng=rng); frames[nm] = (dn, tr)
        if k == 0:
            axf.imshow(np.log1p(dn), cmap="gray", extent=(-9.6, 9.6, -5.4, 5.4)); axf.set_title("Simulated sensor frame, straight gaze, both eyes (log scale, 1920×1080, 10 µm px)  |  eye images split at x = 0")
            axf.set_xlabel("sensor x (mm)"); axf.set_ylabel("sensor y (mm)")
        ax = fig.add_subplot(gs[1, k]); t = tr["L"]; (x1, y1), (x4, y4) = t["P1"], t["P4"]; cx, cy = int((x1+x4)/2), int((y1+y4)/2)
        ax.imshow(dn[cy-45:cy+46, cx-150:cx+151], cmap="inferno", vmax=40, extent=(-150, 150, 45, -45), aspect="equal")
        ax.annotate("P1 (saturated colour scale)", (x1-cx, y1-cy), (x1-cx-10, -30), color="w", fontsize=7, ha="center", arrowprops=dict(arrowstyle="->", color="w", lw=.6))
        ax.annotate("P4", (x4-cx, y4-cy), (x4-cx, -30), color="w", fontsize=7, ha="center", arrowprops=dict(arrowstyle="->", color="w", lw=.6))
        ax.set_title(f"left-eye crop, gaze {nm} (colour scale clipped at 40 DN)", fontsize=8); ax.set_xlabel("px")
    fig.tight_layout(); fig.savefig(f'../results/sim_frames{SUF}.png', dpi=130); plt.close()
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'frames': sys.exit()
    d0, t0 = frames["straight (0°,0°)"]
    res['detect_straight'] = {e: {k: (None if v is None else [round(float(q), 3) for q in v]) for k, v in detect(d0, e).items()} for e in ("L", "R")}
    res['truth_straight'] = {e: {k: [round(float(q), 3) for q in v] for k, v in t0[e].items()} for e in ("L", "R")}
    res['P1_peak_DN'] = float(d0.max()); sep = np.array(t0['L']['P1']) - np.array(t0['L']['P4']); res['P1P4_separation_px_straight'] = sep.tolist()
    # ---- 2. calibration (5x5, +-12 deg) and test (7x7, +-15 deg) with noise; left eye
    def acquire(grid, eye="L", noise=True, dz=0.0):
        F, G = [], []
        for ty in grid:
            for tx in grid:
                p1, p4 = gaze_glints(eye, tx, ty); p1 = p1 + [0, 0, dz]; p4 = p4 + [0, 0, dz]
                dn, tr = render({eye: (p1, p4)}, noise=noise, rng=rng); dt = detect(dn, eye)
                if dt["P4"] is None: continue
                F.append(feature(dt)); G.append((tx, ty))
        return np.array(F), np.array(G, float)
    cal = np.linspace(-12, 12, 5); tst = np.linspace(-15, 15, 7)
    Fc, Gc = acquire(cal); A = design_matrix(Fc); coef = np.linalg.lstsq(A, Gc, rcond=None)[0]
    Ft, Gt = acquire(tst); pred = design_matrix(Ft)@coef; err = pred - Gt; e = np.hypot(err[:, 0], err[:, 1])
    res['n_cal'] = len(Fc); res['n_test'] = len(Ft); res['gaze_error_rms_deg'] = float(np.sqrt((e**2).mean())); res['gaze_error_max_deg'] = float(e.max())
    res['gaze_error_rms_inside_12deg'] = float(np.sqrt((e[np.max(np.abs(Gt), 1) <= 12]**2).mean()))
    # sensitivity (deg per mm of P1-P4 vector) from calibration
    res['gain_deg_per_mm_yaw_from_dx_pitch_from_dy'] = [float(coef[1, 1]), float(coef[2, 0])]
    # ---- 3. precision: repeated noisy frames at fixed gaze
    p1, p4 = gaze_glints("L", 5, 5); f_rep = []
    for i in range(200):
        dn, _ = render({"L": (p1, p4)}, noise=True, rng=rng); dt = detect(dn, "L"); f_rep.append(feature(dt))
    f_rep = np.array(f_rep); gp = design_matrix(f_rep)@coef
    res['precision_deg_std'] = gp.std(0).tolist(); res['centroid_P1P4_std_px'] = (f_rep.std(0)*M/PX).tolist()
    # ---- 4. depth (head-position) sensitivity: eye moves +-1, +-2 mm along the camera axis
    dz_tab = []
    for dz in (-2, -1, 0, 1, 2):
        Fz, Gz = acquire(np.linspace(-10, 10, 3), dz=dz); er = design_matrix(Fz)@coef - Gz
        dz_tab.append((dz, float(np.sqrt((er**2).sum(1).mean()))))
    res['depth_shift_gaze_rms_deg'] = dz_tab
    # ---- 5. lateral head shift (+-0.5 mm) is common to P1 and P4: test with +-0.5 mm shift in x of both glints
    lat = []
    for dx in (-0.5, 0.5):
        F2, G2 = [], []
        for ty in (-10, 0, 10):
            for tx in (-10, 0, 10):
                p1, p4 = gaze_glints("L", tx, ty); sh = np.array([dx, 0, 0])
                dn, _ = render({"L": (p1+sh, p4+sh)}, noise=True, rng=rng); dt = detect(dn, "L"); F2.append(feature(dt)); G2.append((tx, ty))
        er = design_matrix(np.array(F2))@coef - np.array(G2, float); lat.append((dx, float(np.sqrt((er**2).sum(1).mean()))))
    res['lateral_shift_gaze_rms_deg'] = lat
    # ---- figure: gaze error map + P1-P4 vs gaze
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.3))
    ax[0].quiver(Gt[:, 1], Gt[:, 0], err[:, 1], err[:, 0], angles='xy', scale_units='xy', scale=0.05, color='tab:red'); ax[0].plot(Gt[:, 1], Gt[:, 0], 'k.', ms=3)
    ax[0].set_title(f"gaze error (arrows ×20), RMS {res['gaze_error_rms_deg']:.3f}°, max {res['gaze_error_max_deg']:.3f}°", fontsize=9); ax[0].set_xlabel("true yaw (deg)"); ax[0].set_ylabel("true pitch (deg)"); ax[0].set_aspect('equal')
    ax[1].scatter(Ft[:, 0], Ft[:, 1], c=Gt[:, 1], s=12); ax[1].set_title("P1−P4 feature (mm in eye space), colour = yaw", fontsize=9); ax[1].set_xlabel("dx (mm)"); ax[1].set_ylabel("dy (mm)")
    ax[2].plot([d for d, _ in dz_tab], [v for _, v in dz_tab], 'o-'); ax[2].set_title("gaze error vs eye depth shift", fontsize=9); ax[2].set_xlabel("depth shift (mm)"); ax[2].set_ylabel("RMS gaze error (deg)")
    fig.tight_layout(); fig.savefig(f'../results/sim_analysis{SUF}.png', dpi=130); plt.close()
    json.dump(res, open(f'../results/sim_summary{SUF}.json', 'w'), indent=1, default=float); print(json.dumps(res, indent=1, default=float))
