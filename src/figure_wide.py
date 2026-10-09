"""Figures for the wide stock search: design-4A layout and Design 3 vs new designs (spot vs eye depth)."""
import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import fastchan as FC
from raytrace import trace, to_plane, index

C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]   # categorical slots 1-4 (validated default palette)
INK, MUTED = "#0b0b0b", "#52514e"


def load(n):
    return json.load(open(f'../results/{n}.json'))


def layout(name, title, out):
    P = load(name); cfg = [tuple(c) for c in P['cfg']]
    r, half = P['D'] / 2, P['half']
    S, zs, lz = FC.build(cfg, P['ts'], P['gap'], P['b'], r, half)
    def sag(s, y): return s.z + 0 * y if np.isinf(s.R) else s.z + s.R - np.sign(s.R) * np.sqrt(s.R ** 2 - y ** 2)
    fig, ax = plt.subplots(figsize=(15, 5.2))
    yv = np.linspace(-1, 1, 80)
    for s0, s1 in zip(S[:-1], S[1:]):
        if s0.after != "air" and s0.kind != "stop":
            h = min(s0.ap[2], s1.ap[2]) / 0.9 if (s0.ap and s1.ap) else 14
            if np.isinf(s0.R) and np.isinf(s1.R): h = 14
            yy = yv * h
            ax.add_patch(Polygon(np.column_stack([np.r_[sag(s0, yy), sag(s1, yy)[::-1]], np.r_[yy, yy[::-1]]]),
                                 closed=True, fc="#9cc9e8", ec="#1f4e79", lw=.7, alpha=.85))
    for (xo, col) in [(-5.8, C[1]), (0.0, C[2]), (5.8, C[0])]:
        T = np.array([[-half - r, 0, 0], [-half, 0, 0], [-half + r, 0, 0]])
        P3 = np.tile([-half + xo, 0, -P['Lo']], (3, 1)); D3 = T - P3; D3 /= np.linalg.norm(D3, axis=1)[:, None]
        Pc, Dc = to_plane(P3, D3, 0.0), D3; n = 1.0; pts = [[(Pc[k, 2], Pc[k, 0])] for k in range(3)]
        for s in S:
            Pc, Dc, al = trace(Pc, Dc, [s], 0.85, n)
            if s.kind != "stop": n = index(s.after, 0.85)
            for k in range(3): pts[k].append((Pc[k, 2], Pc[k, 0]))
        Q = to_plane(Pc, Dc, zs)
        for k in range(3): pts[k].append((Q[k, 2], Q[k, 0])); ax.plot(*np.array(pts[k]).T, color=col, lw=.8)
    ax.plot([0, 0], [-16, -half - r], color=INK, lw=3); ax.plot([0, 0], [-half + r, half - r], color=INK, lw=3)
    ax.plot([0, 0], [half + r, 16], color=INK, lw=3)
    ax.plot([zs, zs], [-9.6, 9.6], color=MUTED, lw=5)
    for (z0, z1, el, dia), (nm, fl) in zip(lz, cfg):
        ax.text(0.5 * (z0 + z1), 0.45 * dia / 0.9 + 1.5, nm + (" (rev.)" if fl else ""), fontsize=8, ha="center", color=INK)
    ax.text(zs, 10.5, "sensor", fontsize=8, ha="center", color=INK)
    ax.text(0, 17, f"stop: 2 holes Ø{2*r:.1f} at ±{half:.2f} mm", fontsize=8, ha="left", color=INK)
    ax.set_xlim(-8, zs + 8); ax.set_ylim(-27, 27); ax.grid(alpha=.2); ax.set_ylabel("x (mm)"); ax.set_xlabel("z from stop (mm)")
    ax.set_title(title, fontsize=9, color=INK)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)


def depth_fig(out):
    names = [("design3_final", "Design 3 (Ø12, 1.0× light)"), ("design4A_D10", "Design 4A, Ø10.5 plate (1.07×)"),
             ("design4A_D12", "Design 4A, Ø12.6 plate (1.5×)"), ("design4A", "Design 4A, Ø14.7 plate (2.0×)")]
    dz = np.array([-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    for (nm, lab), col in zip(names, C):
        P = load(nm); cfg = [tuple(c) for c in P['cfg']]
        mean, mx = [], []
        for d in dz:
            q = FC.metrics(cfg, P['ts'], P['gap'], P['b'], P['Lo'] + d, P['D'] / 2, P['half'], n=16)
            mean.append(q['rms'].mean()); mx.append(q['rms'].max())
        ax[0].plot(dz, mean, '-o', color=col, lw=2, ms=4, label=lab)
        ax[1].plot(dz, mx, '-o', color=col, lw=2, ms=4, label=lab)
    for a, t in zip(ax, ["mean RMS spot over 9 fields (µm)", "worst-field RMS spot (µm)"]):
        a.set_xlabel("eye depth shift (mm, + = away from camera)"); a.set_title(t, fontsize=10, color=INK)
        a.grid(alpha=.25); a.axhline(10, color=MUTED, lw=.8, ls=":")
        for sp in ("top", "right"): a.spines[sp].set_visible(False)
    ax[0].legend(fontsize=8, frameon=False)
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)


if __name__ == "__main__":
    layout("design4A", "Design 4A: LB1199 + AC508-150-B + LF1988 (rev.) + AC254-075-B, eye→first lens 175.6 mm; "
           "rays for the left-eye channel (orange/green/blue = eye field −5.8/0/+5.8 mm)", "../results/design4A_layout.png")
    layout("design3B", "Design 3B: LB1199 + AC254-150 + AC254-075-B, eye→first lens 150 mm", "../results/design3B_layout.png")
    depth_fig("../results/wide_depth.png")
