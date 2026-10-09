"""Wide stock-lens search (2-, 3- and 4-element objectives) for the Design-3 channel geometry.

Stage 1 (screen): every ordered combination of oriented stock elements.  For each, a grid of air gaps is
solved paraxially for m = -M_T (object distance Lo and sensor distance b in closed form), filtered for
eye distance, back focus, mechanical clearance and paraxial aperture clearance, and the best few grid
points are ray-traced (focus solved) at the screening NA.  Writes ../results/wide_screen_<n>.json.

usage: python3 search_wide.py screen 2|3     |  python3 search_wide.py screen4 (extends best triples)
"""
import sys, json, itertools, time, numpy as np
from multiprocessing import Pool
from stock import LIB, element
from raytrace import index
import fastchan as FC

M_T = 0.545                      # paraxial screening magnification (allowed window 0.53-0.59)
NA0 = 6.0 / 196.005              # Design 3 stop half-angle (D = 12 mm at 196 mm)
import os
NA_K = float(os.environ.get('NA_K', 1.2))
NA_SCREEN = NA_K * NA0           # screen at NA_K^2 x Design-3 light (default 1.44x)
EYE_MIN, EYE_MAX = 150.0, 205.0  # eye -> first lens vertex
B_MIN, B_MAX = 8.0, 170.0
TS = 0.3
N_BK7 = index("N-BK7", 0.85)
SYM = {"LB1471", "LB1294", "LB1199", "LD1613", "LD1464", "LD1170"}
GRID = np.array([3, 6, 10, 15, 22, 30, 40, 52, 66, 82, 100, 120, 145.0])

ORIENTED = [(nm, fl) for nm in LIB for fl in (0, 1) if not (fl and nm in SYM)]
EM = {e: FC.elem_matrix(*e) for e in ORIENTED}


def sag(R, h):
    if not np.isfinite(R): return 0.0
    return R - np.sign(R) * np.sqrt(max(R * R - h * h, 0.0))


def gmin(ea, eb, clear=0.5):
    la, da = element(*ea); lb, db = element(*eb)
    h = 0.5 * min(da, db)
    return max(clear, max(sag(la[-1][0], x) - sag(lb[0][0], x) + clear for x in np.linspace(0, h, 9)))


def paraxial_grid(cfg, NA=NA_SCREEN, m=M_T, ts=TS):
    """Return list of feasible (gaps, Lo, b, r, half, margin) sorted by aperture margin."""
    n = len(cfg)
    gl = [GRID[GRID >= gmin(a, b_)] for a, b_ in zip(cfg[:-1], cfg[1:])]
    if any(len(g) == 0 for g in gl):
        return []
    if n > 1:
        G = np.array(list(itertools.product(*gl)))       # (P, n-1)
    else:
        G = np.zeros((1, 0))
    P = len(G)
    K = FC.Tm(np.full(P, FILT_RED + ts))                 # stop -> first vertex
    surf_maps = []                                       # stop -> each element front/back
    for k, e in enumerate(cfg):
        Em, T, dia = EM[e]
        surf_maps.append((K.copy(), dia))
        K = np.einsum('ij,pjk->pik', Em, K)
        surf_maps.append((K.copy(), dia))
        if k < n - 1:
            K = np.einsum('pij,pjk->pik', FC.Tm(G[:, k]), K)
    a, bb, c, d = K[:, 0, 0], K[:, 0, 1], K[:, 1, 0], K[:, 1, 1]
    with np.errstate(divide='ignore', invalid='ignore'):
        v = (-m - a) / c
        Lo = (bb + v * d) / m
    b = v - 1.0 / N_BK7 - 0.5 - 0.0      # cover glass (1 mm, reduced) + 0.5 mm gap: v is reduced distance
    b = v - FC.COVER_T / N_BK7 - FC.COVER_GAP
    eye = Lo + FC.FILT_T + ts
    ok = np.isfinite(v) & (eye >= EYE_MIN) & (eye <= EYE_MAX) & (b >= B_MIN) & (b <= B_MAX)
    if not ok.any():
        return []
    r = NA * Lo; half = np.maximum(6.5, r + 0.3)
    # aperture margin: worst over surfaces of (allowed - needed), needed = chief(o) + k*|alpha'| r
    margin = np.full(P, np.inf)
    corners = [(-5.8, 7.6), (5.8, 7.6), (-5.8, -7.6), (5.8, -7.6)]
    for Mk, dia in surf_maps:
        ap = 0.45 * dia
        al = Mk[:, 0, 0]; be = Mk[:, 0, 1]
        A = al + be / Lo; Bo = be / Lo
        need_c = np.abs(A * (-half) - Bo * (-half)) + 0.5 * np.abs(A) * r    # centre field: half the beam inside (coarse; real rays judge vignetting)
        need = need_c
        for dx, dy in corners:
            ox, oy = -half + dx, dy
            ch = np.hypot(A * (-half) - Bo * ox, -Bo * oy)
            need = np.maximum(need, ch)                                       # corners: chief ray inside
        margin = np.minimum(margin, ap - need)
    ok &= margin >= 0
    idx = np.where(ok)[0]
    res = [(G[i].tolist(), float(Lo[i]), float(b[i]), float(r[i]), float(half[i]), float(margin[i])) for i in idx]
    return res


FILT_RED = FC.FILT_T / N_BK7


def cost_of(res, m_target=None):
    if res is None:
        return 1e6
    rms, fr, m = res['rms'], res['fr'], res['m']
    c = res['c']
    pen = 1500 * max(0, abs(m - 0.56) - 0.03) + 150 * (1 - fr).max()
    pen += 300 * max(0, 0.3 - c[:, 0].min()) + 300 * max(0, c[:, 0].max() - 9.3)
    if not res.get('mech', True):
        pen += 1e3
    return rms.mean() + 0.3 * rms.max() + pen


def screen_one(cfg, kmax=20, n=6):
    pts = paraxial_grid(cfg)
    if not pts:
        return None
    # sample up to kmax points spread over the feasible set
    if len(pts) > kmax:
        sel = np.linspace(0, len(pts) - 1, kmax).round().astype(int)
        pts = [pts[i] for i in sel]
    best = None
    for gaps, Lo, b, r, half, mg in pts:
        try:
            res = FC.metrics(cfg, TS, gaps, b, Lo, r, half, n=n, solve_focus=True)
        except Exception:
            res = None
        cst = cost_of(res)
        if best is None or cst < best[0]:
            best = (cst, gaps, Lo, b + (res['dz'] if res else 0.0), r, half,
                    None if res is None else float(res['rms'].mean()), None if res is None else float(res['rms'].max()))
    return dict(cfg=cfg, cost=best[0], gaps=best[1], Lo=best[2], b=best[3], r=best[4], half=best[5],
                rms_mean=best[6], rms_max=best[7], nfeas=len(pts))


def run(cfgs, tag, procs=2):
    t0 = time.time(); out = []
    with Pool(procs) as p:
        for i, r in enumerate(p.imap_unordered(screen_one, cfgs, chunksize=64)):
            if r is not None and r['cost'] < 1e5:
                out.append(r)
            if i % 5000 == 0:
                print(tag, i, len(cfgs), len(out), round(time.time() - t0), 's', flush=True)
    out.sort(key=lambda r: r['cost'])
    json.dump(out, open(f'../results/wide_screen_{tag}.json', 'w'))
    print('done', tag, len(out), round(time.time() - t0), 's')
    for r in out[:15]:
        print(round(r['cost'], 2), r['cfg'], round(r['Lo'] + 3.3, 1), r['rms_mean'] and round(r['rms_mean'], 2), r['rms_max'] and round(r['rms_max'], 2))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "screen":
        n = int(sys.argv[2])
        cfgs = [list(c) for c in itertools.product(ORIENTED, repeat=n)]
        print(len(ORIENTED), 'oriented elements ->', len(cfgs), 'configs', flush=True)
        run(cfgs, str(n))
    elif mode == "screen4":
        # insert one more oriented element (any position) into the best refined triples
        src, ntop = sys.argv[2], int(sys.argv[3])
        base = [[tuple(c) for c in r['cfg']] for r in json.load(open(src)) if len(r['cfg']) == 3][:ntop]
        cfgs = []
        for b in base:
            for pos in range(4):
                for e in ORIENTED:
                    c = b[:pos] + [e] + b[pos:]
                    if c not in cfgs: cfgs.append(c)
        print(len(cfgs), 'four-element configs', flush=True)
        run(cfgs, '4')
