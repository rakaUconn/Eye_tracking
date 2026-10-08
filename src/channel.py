"""Part-B model: one unfolded channel (stop -> doublet -> filter -> cover glass -> sensor)."""
import numpy as np
from raytrace import Surf, trace, to_plane, index

WLS = (0.84, 0.85, 0.86)
FILT_T, COVER_T = 3.0, 1.0      # placeholders: FBH850-10 ~2-3 mm, sensor cover glass TBD (verify)

def build(p, stop_x=-6.5, stop_r=3.125, wl=0.85):
    """p: dict R1,R2,R3,t1,t2,ts,g1,g2. Lens axis at x=0, stop centred at x=stop_x (z=0)."""
    z = 0.0
    S = [Surf(0.0, kind="stop", ap=(stop_x, 0, stop_r))]
    z += p["ts"]
    S.append(Surf(z, p["R1"], p["g1"], ap=(0, 0, 11.5)));  z += p["t1"]
    S.append(Surf(z, p["R2"], p["g2"], ap=(0, 0, 11.5)));  z += p["t2"]
    S.append(Surf(z, p["R3"], "air", ap=(0, 0, 11.5)))
    return S, z

def fields(m=0.55, ex=11.6, ey=15.2, xc=-6.5, n=3):
    xs = xc + np.linspace(-ex/2, ex/2, n); ys = np.linspace(-ey/2, ey/2, n)
    return np.array([(x, y) for y in ys for x in xs])

def pupil(stop_x, stop_r, n=14):
    g = np.linspace(-1, 1, n)
    X, Y = np.meshgrid(g, g); m = X**2+Y**2 <= 1
    return stop_x + stop_r*X[m], stop_r*Y[m]

def rays_from(obj_xy, Lo, stop_x, stop_r, n=14):
    px, py = pupil(stop_x, stop_r, n)
    P = np.column_stack([np.full(len(px), obj_xy[0]), np.full(len(px), obj_xy[1]), np.full(len(px), -Lo)])
    T = np.column_stack([px, py, np.zeros(len(px))])
    D = T - P; D /= np.linalg.norm(D, axis=1)[:, None]
    return P, D

def image_spots(p, Lo, zimg_off, wl=0.85, **kw):
    """returns dict field_idx -> (x,y) arrays at the image plane and chief centroid."""
    S, zlast = build(p, **{k: v for k, v in kw.items() if k in ("stop_x", "stop_r")})
    stop_x = kw.get("stop_x", -6.5); stop_r = kw.get("stop_r", 3.125)
    F = kw["F"]
    out = []
    for f in F:
        P, D = rays_from(f, Lo, stop_x, stop_r)
        # start on stop plane, in air (propagate object -> stop plane)
        P0 = to_plane(P, D, 0.0)
        Pn, Dn, al = trace(P0, D, S[1:], wl)
        # filter+cover: plane-parallel plates shift (apply analytic by tracing them)
        zl = zlast
        plates = [Surf(zl, np.inf, "N-BK7"), Surf(zl+FILT_T, np.inf, "air"),
                  Surf(zl+FILT_T+0.5, np.inf, "N-BK7"), Surf(zl+FILT_T+0.5+COVER_T, np.inf, "air")]
        Pn, Dn, al2 = trace(Pn, Dn, plates, wl)
        zi = zl + FILT_T + 0.5 + COVER_T + zimg_off
        Q = to_plane(Pn, Dn, zi)
        a = al & al2
        out.append(Q[a][:, :2])
    return out
