"""Fast, parameter-explicit version of the Design-3 channel model (same geometry and metric as
stock_final.metrics + multi.build_multi): off-axis stop hole (radius r, centre x = -half) on the
3 mm filter, stock elements, cover glass, sensor.  All 9 fields are traced in one call per wavelength,
and the sensor focus can be solved in closed form.  Also: paraxial matrices for screening."""
import numpy as np
from raytrace import Surf, trace, to_plane, index
from channel import rays_from, pupil
from stock import element
import stock_final as SF

EX, EY = 11.6, 15.2
WLS = (0.84, 0.85, 0.86)
FILT_T, FILT_G, COVER_T, COVER_GAP = SF.FILT_T, SF.FILT_G, SF.COVER_T, SF.COVER_GAP


def fields(half):
    xs = -half + np.linspace(-EX / 2, EX / 2, 3); ys = np.linspace(-EY / 2, EY / 2, 3)
    return np.array([(x, y) for y in ys for x in xs])


def build(cfg, ts, gaps, b, r, half):
    gaps = np.atleast_1d(gaps)
    S = [Surf(0.0, kind="stop", ap=(-half, 0, r)), Surf(0.0, np.inf, FILT_G), Surf(FILT_T, np.inf, "air")]
    z = FILT_T + ts
    lens_z = []
    for k, (name, flip) in enumerate(cfg):
        el, dia = element(name, flip)
        z0 = z
        for R, t, med in el:
            S.append(Surf(z, R, med, ap=(0, 0, 0.45 * dia))); z += t
        lens_z.append((z0, z, el, dia))
        if k < len(cfg) - 1:
            z += gaps[k]
    zc = z + b
    S += [Surf(zc, np.inf, "N-BK7"), Surf(zc + COVER_T, np.inf, "air")]
    return S, zc + COVER_T + COVER_GAP, lens_z


def mech_ok(lens_z, min_clear=0.5):
    """centre and edge clearance between consecutive elements."""
    def sag(R, h):
        if not np.isfinite(R): return 0.0
        return R - np.sign(R) * np.sqrt(max(R * R - h * h, 0.0))
    for (a0, a1, ea, da), (b0, b1, eb, db) in zip(lens_z[:-1], lens_z[1:]):
        h = 0.5 * min(da, db)
        for hh in np.linspace(0, h, 5):
            if (b0 + sag(eb[0][0], hh)) - (a1 + sag(ea[-1][0], hh)) < min_clear:
                return False
    return True


def trace_all(cfg, ts, gaps, b, Lo, r, half, n=8, wls=WLS):
    S, zs, lz = build(cfg, ts, gaps, b, r, half)
    F = fields(half)
    P, D, fid = [], [], []
    for i, f in enumerate(F):
        p, d = rays_from(f, Lo, -half, r, n); P.append(p); D.append(d); fid.append(np.full(len(p), i))
    P = np.vstack(P); D = np.vstack(D); fid = np.concatenate(fid)
    P0 = to_plane(P, D, 0.0)
    out = []
    for w in wls:
        Q, Dd, al = trace(P0, D, S, w)
        Q = to_plane(Q, Dd, zs)
        out.append((Q, Dd, al))
    N0 = len(pupil(-half, r, n)[0])
    return out, fid, zs, N0, lz


def metrics(cfg, ts, gaps, b, Lo, r, half, n=8, solve_focus=False, wls=WLS):
    """returns dict(rms[9] um, c[9,2], m, fr[9], dz) or None.  Same definitions as stock_final.metrics."""
    out, fid, zs, N0, lz = trace_all(cfg, ts, gaps, b, Lo, r, half, n, wls)
    alive = np.all([o[2] for o in out], axis=0) if False else None
    fr = np.min([[np.sum(o[2] & (fid == i)) / N0 for i in range(9)] for o in out], axis=0)
    if np.any(fr * N0 < 6):
        return None
    dz = 0.0
    if solve_focus:
        A = Bq = 0.0
        for i in range(9):
            pts, slopes = [], []
            for o in out:
                k = o[2] & (fid == i)
                pts.append(o[0][k][:, :2]); slopes.append(o[1][k][:, :2] / o[1][k][:, 2:3])
            c0 = pts[1].mean(0); s0 = slopes[1].mean(0)
            a = np.vstack(pts) - c0; s = np.vstack(slopes) - s0
            A += (s * s).sum(1).mean(); Bq += (a * s).sum(1).mean()
        dz = -Bq / A
    rms = np.zeros(9); c = np.zeros((9, 2))
    for i in range(9):
        pts = []
        for o in out:
            k = o[2] & (fid == i)
            q = o[0][k]; d = o[1][k]
            pts.append(q[:, :2] + dz * d[:, :2] / d[:, 2:3])
        cc = pts[1].mean(0); c[i] = cc
        a = np.vstack(pts) - cc; rms[i] = np.sqrt((a ** 2).sum(1).mean()) * 1e3
    m = abs((c[3, 0] - c[5, 0]) / EX + (c[1, 1] - c[7, 1]) / EY) / 2
    return dict(rms=rms, c=c, m=m, fr=fr, dz=dz, mech=mech_ok(lz))


def mtf25(cfg, ts, gaps, b, Lo, r, half, n=20):
    """geometric x diffraction MTF at 25 lp/mm (same estimator as refine3.py)."""
    out, fid, zs, N0, lz = trace_all(cfg, ts, gaps, b, Lo, r, half, n)
    # working NA from the centre field at 850 nm
    o = out[1]; k = o[2] & (fid == 4)
    NA = np.sin(np.ptp(np.arctan2(o[1][k][:, 0], o[1][k][:, 2])) / 2)
    fc = 2 * NA / 0.85e-3; rr = 25 / fc; dm = 2 / np.pi * (np.arccos(rr) - rr * np.sqrt(1 - rr * rr))
    res = np.zeros((9, 2))
    for i in range(9):
        pts = [o_[0][o_[2] & (fid == i)][:, :2] for o_ in out]
        allp = np.vstack(pts) - pts[1].mean(0)
        for ax in (0, 1):
            res[i, ax] = abs(np.exp(-2j * np.pi * 25 * allp[:, ax]).mean()) * dm
    return res, 1 / (2 * NA)


# ------------------------------------------------------------------ paraxial
def elem_matrix(name, flip, wl=0.85):
    """(y, n u) matrix from first to last vertex of an element, and its thickness."""
    el, dia = element(name, flip)
    M = np.eye(2); n = 1.0; T = 0.0
    for R, t, med in el:
        n2 = index(med, wl)
        P = (n2 - n) / R if np.isfinite(R) else 0.0
        M = np.array([[1, 0], [-P, 1]]) @ M
        if t:
            M = np.array([[1, t / n2], [0, 1]]) @ M; T += t
        n = n2
    return M, T, dia


def Tm(d):
    """free-space transfer for an array of distances -> (...,2,2)"""
    d = np.asarray(d, float)
    out = np.zeros(d.shape + (2, 2)); out[..., 0, 0] = 1; out[..., 1, 1] = 1; out[..., 0, 1] = d
    return out


def metrics_depth(cfg, ts, gaps, b, Lo, r, half, dzs=(-1.0, 0.0, 1.0), w=(0.5, 1.0, 0.5), n=8, solve_focus=True):
    """Common sensor focus for several eye depths (Lo + dz); focus solved for the weighted sum of mean RMS^2.
    Returns (list of per-depth metric dicts, dz_focus)."""
    traced = [trace_all(cfg, ts, gaps, b, Lo + d, r, half, n) for d in dzs]
    dzf = 0.0
    if solve_focus:
        A = Bq = 0.0
        for (out, fid, zs, N0, lz), wt in zip(traced, w):
            for i in range(9):
                pts, slopes = [], []
                for o in out:
                    k = o[2] & (fid == i)
                    if k.sum() < 3: return None, 0.0
                    pts.append(o[0][k][:, :2]); slopes.append(o[1][k][:, :2] / o[1][k][:, 2:3])
                c0 = pts[1].mean(0); s0 = slopes[1].mean(0)
                a = np.vstack(pts) - c0; s = np.vstack(slopes) - s0
                A += wt * (s * s).sum(1).mean(); Bq += wt * (a * s).sum(1).mean()
        dzf = -Bq / A
    return [metrics(cfg, ts, gaps, b + dzf, Lo + d, r, half, n=n) for d in dzs], dzf
