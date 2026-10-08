import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
from raytrace import Surf, trace, to_plane, index
import opt2, opt_stock as O
from channel import rays_from, FILT_T, COVER_T

XC, SR = -6.5, 3.125
def plates(z0): return [Surf(z0, np.inf, "N-BK7"), Surf(z0+FILT_T, np.inf, "air"), Surf(z0+FILT_T+.5, np.inf, "N-BK7"), Surf(z0+FILT_T+.5+COVER_T, np.inf, "air")]
def sag(s, y):
    if np.isinf(s.R): return s.z + 0*y
    return s.z + s.R - np.sign(s.R)*np.sqrt(s.R**2 - y**2)
def path(S, zl, Lo, zoff, fields, wl=0.85, n=7):
    """return list of polylines (x,z) per ray, z measured from the stop plane."""
    allS = S + plates(zl); zi = zl + FILT_T + .5 + COVER_T + zoff
    out = []
    for f in fields:
        P, D = rays_from(f, Lo, XC, SR, 3)
        # pick 3 rays in tangential plane (y=0 pupil row): lowest, centre, highest x
        sel = [i for i in range(len(P)) if abs(D[i, 1]*Lo) < 1e-6 or True]
        px = P + 0
        T = np.array([[XC-SR, 0, 0], [XC, 0, 0], [XC+SR, 0, 0]]); P3 = np.tile([f[0], f[1], -Lo], (3, 1)); D3 = T-P3; D3 /= np.linalg.norm(D3, axis=1)[:, None]
        pts = [[(P3[k, 0], -Lo)] for k in range(3)]
        Pc, Dc = to_plane(P3, D3, 0.0), D3; n_med = 1.0
        for k in range(3): pts[k].append((Pc[k, 0], 0.0))
        for s in allS:
            Pc, Dc, al = trace(Pc, Dc, [s], wl, n_med); n_med = index(s.after, wl)
            for k in range(3): pts[k].append((Pc[k, 0], Pc[k, 2]))
        Q = to_plane(Pc, Dc, zi)
        for k in range(3): pts[k].append((Q[k, 0], zi))
        out.append(pts)
    return out, zi

def draw_lenses(ax, S, ap):
    # glass groups: consecutive surfaces with non-air medium after the first
    y = np.linspace(-1, 1, 60)
    for a, b in zip(S[:-1], S[1:]):
        if a.after != "air":
            h = min(a.ap[2], b.ap[2]); yy = y*h
            xa = np.concatenate([sag(a, yy), sag(b, yy)[::-1]]); ya = np.concatenate([yy, yy[::-1]])
            ax.add_patch(Polygon(np.column_stack([xa, ya]), closed=True, fc="#9cc9e8", ec="#1f4e79", lw=.8, alpha=.8))
def unfolded(ax, S, zl, Lo, zoff, title):
    fields = [np.array([XC-5.8, 0.]), np.array([XC, 0.]), np.array([XC+5.8, 0.])]
    paths, zi = path(S, zl, Lo, zoff, fields)
    # plot in lens frame: horizontal = z (from stop), vertical = x
    draw_lenses(ax_proxy := type("A", (), {"add_patch": lambda self, p: None})(), S, None)
    cols = ["tab:red", "tab:green", "tab:blue"]
    for pts, c in zip(paths, cols):
        for r in pts:
            r = np.array(r); ax.plot(r[:, 1], r[:, 0], color=c, lw=.8)
    # lenses drawn with z horizontal / x vertical
    yv = np.linspace(-1, 1, 60)
    for a, b in zip(S[:-1], S[1:]):
        if a.after != "air":
            h = min(a.ap[2], b.ap[2]); yy = yv*h
            za = np.concatenate([sag(a, yy), sag(b, yy)[::-1]]); xa = np.concatenate([yy, yy[::-1]])
            ax.add_patch(Polygon(np.column_stack([za, xa]), closed=True, fc="#9cc9e8", ec="#1f4e79", lw=.8, alpha=.85))
    for z0, z1, col in [(zl, zl+FILT_T, "#d9a0d9"), (zl+FILT_T+.5, zl+FILT_T+.5+COVER_T, "#bbbbbb")]:
        ax.add_patch(Rectangle((z0, -9), z1-z0, 18, fc=col, ec="k", lw=.5, alpha=.8))
    ax.add_patch(Rectangle((-1, XC-SR-0.0), 0.8, 2*SR, fc="none", ec="none"))
    ax.plot([0, 0], [-12, XC-SR], 'k', lw=3); ax.plot([0, 0], [XC+SR, 12], 'k', lw=3)   # stop plate
    ax.plot([zi, zi], [-9.6, 0], color="darkorange", lw=4); ax.plot([zi, zi], [0, 9.6], color="seagreen", lw=4)
    ax.set_xlabel("z from stop (mm)  → toward sensor"); ax.set_ylabel("x (mm)"); ax.set_title(title, fontsize=9); ax.set_xlim(-8, zi+6)
    ax.set_ylim(-12, 12); ax.grid(alpha=.2)
    ax.annotate("stop Ø6.25\n@ x = –6.5", (0, XC), (6, -11.5), fontsize=7, arrowprops=dict(arrowstyle="->", lw=.6))
    ax.text(zi-2, 10.2, "sensor: green half = left eye, orange half = right eye", fontsize=7, ha="right")

fig = plt.figure(figsize=(13, 11)); gs = fig.add_gridspec(3, 1, height_ratios=[1.25, 1, 1])
# ---------- (a) folded top view
ax = fig.add_subplot(gs[0]); ax.set_aspect("equal")
IPD = 63.0; H = IPD/2; s_o = 30.0; Lo = 149.0
d = json.load(open('../results/two_doublet.json')); v = np.array(d['v']); g = d['glass']
S1, zl1 = opt2.build(v[:8], g)
for sgn in (-1, 1):
    ex = sgn*H
    ax.add_patch(Circle((0, ex), 12, fc="#fff3d6", ec="k", lw=.8)); ax.add_patch(Circle((-6, ex), 3, fc="k"))
    ax.text(0, ex+sgn*15, "left eye" if sgn < 0 else "right eye", fontsize=8, ha="center", va="center")
    ax.plot([0, s_o], [ex, ex], color="r", lw=1)                      # eye -> M1
    ax.plot([s_o, s_o], [ex, sgn*6.5], color="r", lw=1)               # M1 -> V
    ax.plot([s_o, Lo], [sgn*6.5, sgn*6.5], color="r", lw=1)           # V -> stop
    ax.plot([s_o-3, s_o+3], [ex-3, ex+3] if sgn > 0 else [ex+3, ex-3], color="navy", lw=3)   # M1 (45 deg)
    ax.text(s_o, ex+sgn*5, "M1", fontsize=7, ha="center", va="center")
# V prism / knife edge
ax.add_patch(Polygon([[s_o-6.5, 0], [s_o+6.5-6.5+0.0, 6.5], [s_o+0.0, 6.5], [s_o, 0]], fc="none"))
ax.plot([s_o-3, s_o, s_o-3], [-9.5, 0, 9.5], color="navy", lw=3); ax.text(s_o+4, 0, "V-prism\n(knife edge)", fontsize=7, va="center")
# stop plate
ax.plot([Lo, Lo], [-12, -6.5-3.125], 'k', lw=3); ax.plot([Lo, Lo], [-6.5+3.125, 6.5-3.125], 'k', lw=3); ax.plot([Lo, Lo], [6.5+3.125, 12], 'k', lw=3)
ax.text(Lo, 14.5, "dual-hole stop\n(Ø6.25 @ ±6.5)", fontsize=7, ha="center")
# lenses + sensor in same frame (z shifted to Lo)
yv = np.linspace(-1, 1, 60)
for a, b in zip(S1[:-1], S1[1:]):
    if a.after != "air":
        h = min(a.ap[2], b.ap[2]); yy = yv*h
        za = np.concatenate([sag(a, yy), sag(b, yy)[::-1]])+Lo; xa = np.concatenate([yy, yy[::-1]])
        ax.add_patch(Polygon(np.column_stack([za, xa]), closed=True, fc="#9cc9e8", ec="#1f4e79", lw=.8))
zs = Lo + zl1 + FILT_T + .5 + COVER_T + v[9]
ax.add_patch(Rectangle((Lo+zl1, -9), FILT_T, 18, fc="#d9a0d9", ec="k", lw=.5)); 
ax.plot([zs, zs], [-9.6, 0], color="darkorange", lw=5); ax.plot([zs, zs], [0, 9.6], color="seagreen", lw=5)
ax.text(zs+3, 0, "Lux19HS 19.2×10.8 mm\nupper half (x>0, green) = left eye\nlower half (x<0, orange) = right eye", fontsize=7, va="center")
# lens rays (left channel; right mirrored)
fields = [np.array([XC-5.8, 0.]), np.array([XC, 0.]), np.array([XC+5.8, 0.])]
paths, zi = path(S1, zl1, Lo, v[9], fields)
for pts, c in zip(paths, ["tab:red", "tab:green", "tab:blue"]):
    for r in pts:
        r = np.array(r)
        for sgn in (-1, 1): ax.plot(Lo+r[1:, 1], sgn*(-r[1:, 0])*-1 if False else (r[1:, 0] if sgn < 0 else -r[1:, 0]), color=c, lw=.5)
ax.set_xlim(-18, zs+48); ax.set_ylim(-46, 46); ax.set_xlabel("optical axis, z (mm) — top view, unfolded distance eye→stop = 149 mm"); ax.set_ylabel("lateral x (mm)")
ax.set_title("(a) Folded binocular layout, top view: two eyes → M1 mirrors → central V-prism → dual-hole stop → one objective → one split sensor (IPD 63 mm, m = 0.55)", fontsize=9)
# ---------- (b) surrogate, (c) stock
ax2 = fig.add_subplot(gs[1]); unfolded(ax2, S1, zl1, Lo, v[9], "(b) Objective, surrogate custom pair (N-BK7/F2 doublets): RMS spot 4–9 µm (red/green/blue = eye field –5.8 / 0 / +5.8 mm)")
w = json.load(open('../results/stock_winner.json')); cfg = [tuple(c) for c in w['cfg']]
S2, zl2 = O.build(cfg, w['ts'], w['gap'])
ax3 = fig.add_subplot(gs[2]); unfolded(ax3, S2, zl2, w['Lo'], w['zoff'] - O.para_focus(S2, zl2, w['Lo']) + O.para_focus(S2, zl2, w['Lo']), "(c) Objective, Thorlabs stock pair AC254-150 (rev.) + AC254-075-B at 137.3 mm: RMS spot 5–16 µm")
fig.tight_layout(); fig.savefig('../results/optical_system_design.png', dpi=140)
print("ok")
