import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import stock_final as SF, multi
from stock import element
from raytrace import Surf, trace, to_plane, index
from channel import rays_from
P = json.load(open('../results/design3_final.json'))
SF.CFG = [tuple(c) for c in P['cfg']]; SF.SR = P['D']/2; SF.XC = -P['half']
S, zs = multi.build_multi(P['ts'], P['gap'], P['b']); Lo = P['Lo']; XC, SR = SF.XC, SF.SR
def sag(s, y): return s.z + 0*y if np.isinf(s.R) else s.z + s.R - np.sign(s.R)*np.sqrt(s.R**2 - y**2)
fig, ax = plt.subplots(2, 1, figsize=(15, 8.5), gridspec_kw=dict(height_ratios=[1.1, 1]))
fields = [(-5.8, "tab:red"), (0.0, "tab:green"), (5.8, "tab:blue")]
for a, (xl, xr) in zip(ax, [(-8, zs+8), (-6, 40)]):
    yv = np.linspace(-1, 1, 80)
    for s0, s1 in zip(S[:-1], S[1:]):
        if s0.after != "air" and s0.kind != "stop":
            h = min(s0.ap[2] if s0.ap else 12.7, s1.ap[2] if s1.ap else 12.7) if s0.ap and s1.ap else 12.0
            if np.isinf(s0.R) and np.isinf(s1.R): h = 14
            yy = yv*h
            a.add_patch(Polygon(np.column_stack([np.r_[sag(s0, yy), sag(s1, yy)[::-1]], np.r_[yy, yy[::-1]]]), closed=True, fc="#9cc9e8", ec="#1f4e79", lw=.7, alpha=.85))
    for xo, col in fields:
        T = np.array([[XC-SR, 0, 0], [XC, 0, 0], [XC+SR, 0, 0]]); f = np.array([XC+xo, 0.0])
        P3 = np.tile([f[0], 0, -Lo], (3, 1)); D3 = T - P3; D3 /= np.linalg.norm(D3, axis=1)[:, None]
        Pc, Dc = to_plane(P3, D3, 0.0), D3; n = 1.0; pts = [[(Pc[k, 2], Pc[k, 0])] for k in range(3)]
        for s in S:
            Pc, Dc, al = trace(Pc, Dc, [s], 0.85, n)
            if s.kind != "stop": n = index(s.after, 0.85)
            for k in range(3): pts[k].append((Pc[k, 2], Pc[k, 0]))
        Q = to_plane(Pc, Dc, zs)
        for k in range(3): pts[k].append((Q[k, 2], Q[k, 0])); a.plot(*np.array(pts[k]).T, color=col, lw=.8)
    a.plot([0, 0], [-14, XC-SR], 'k', lw=3); a.plot([0, 0], [XC+SR, 14], 'k', lw=3)
    a.plot([zs, zs], [-9.6, 0], color="darkorange", lw=5); a.plot([zs, zs], [0, 9.6], color="seagreen", lw=5)
    a.set_xlim(xl, xr); a.set_ylim(-26 if xr > 100 else -15, 26 if xr > 100 else 15); a.grid(alpha=.2); a.set_ylabel("x (mm)")
ax[0].set_title("Design 3 objective: LBF254-200 (rev.) + AC508-150-B + AC254-150, stop Ø12 mm, eye→first lens 199 mm; green/orange = left/right sensor halves (rays shown for the left-eye channel; red/green/blue = eye field −5.8/0/+5.8 mm)", fontsize=9)
ax[1].set_title("zoom on the stop, filter and first lens", fontsize=9); ax[1].set_xlabel("z from stop (mm)")
names = ["LBF254-200", "AC508-150-B", "AC254-150"]; zl = SF.FILT_T + P['ts']
for zt, nm in [(zl+2.0, "LBF254-200 (rev.)"), (126, "AC508-150-B"), (217, "AC254-150"), (zs-30, "cover glass + sensor")]:
    ax[0].text(zt, 24, nm, fontsize=8, ha="center")

fig.tight_layout(); fig.savefig('../results/design3_layout.png', dpi=140); print("zs", zs)
