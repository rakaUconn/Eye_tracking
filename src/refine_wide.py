"""Stage 2/3 of the wide search.
refine  <tags> <ntop>  : Nelder-Mead on (ts, gaps, Lo) at the screening NA, focus solved; -> wide_refined.json
ladder  <ntop>         : for the best refined configs, raise NA in steps (warm start, re-optimise each step)
                         and keep the largest NA that still meets Design-3 image quality -> wide_ladder.json
"""
import sys, json, numpy as np
from multiprocessing import Pool
from scipy.optimize import minimize
import fastchan as FC
import search_wide as SW

# Design 3 re-evaluated with the same code (n = 20): mean 9.22 / max 12.59 um, vig 0.917, MTF25 min 0.075
REF = dict(mean=9.23, max=12.6, vig=0.90, mtf=0.07)
# depth-robust mode (DEPTH=1): also hold Design 3's +-1 mm eye-depth blur (n=16: mean 13.25/13.94, max 21.9/22.2)
import os
DEPTH = os.environ.get('DEPTH', '0') == '1'
REF_D = dict(mean=13.95, max=22.3)
LAM_D = 0.6


def unpack(u, ng):
    return u[0], np.asarray(u[1:1 + ng]), u[1 + ng]


def make_cost(cfg, NA, n=8):
    ng = len(cfg) - 1
    gm = [SW.gmin(a, b) for a, b in zip(cfg[:-1], cfg[1:])]
    state = {}

    def cost(u):
        ts, gaps, Lo = unpack(u, ng)
        eye = Lo + FC.FILT_T + ts
        if not (0.3 <= ts <= 15 and all(g >= m_ for g, m_ in zip(gaps, gm)) and np.all(gaps <= 150)
                and SW.EYE_MIN <= eye <= SW.EYE_MAX):
            return 1e6
        r = NA * Lo; half = max(6.5, r + 0.3)
        b = state.get('b', 60.0)
        if DEPTH:
            try:
                rs, dzf = FC.metrics_depth(cfg, ts, gaps, b, Lo, r, half, n=n)
            except Exception:
                return 1e6
            if rs is None or any(x is None for x in rs):
                return 1e6
            bb = b + dzf
            if not (SW.B_MIN <= bb <= SW.B_MAX):
                return 1e6
            state['b'] = bb
            cd = [x['rms'].mean() + 0.3 * x['rms'].max() for x in (rs[0], rs[2])]
            return SW.cost_of(rs[1]) + LAM_D * 0.5 * sum(cd)
        try:
            res = FC.metrics(cfg, ts, gaps, b, Lo, r, half, n=n, solve_focus=True)
        except Exception:
            return 1e6
        if res is None:
            return 1e6
        bb = b + res['dz']
        if not (SW.B_MIN <= bb <= SW.B_MAX):
            return 1e6
        state['b'] = bb
        return SW.cost_of(res)
    return cost, state, gm


def optimise(cfg, u0, b0, NA, iters=3, maxiter=400, n=8):
    cost, state, gm = make_cost(cfg, NA, n)
    state['b'] = b0
    u = np.array(u0, float)
    best = (cost(u), u.copy(), state['b'])
    for it in range(iters):
        q = minimize(cost, u, method='Nelder-Mead',
                     options=dict(maxiter=maxiter, xatol=1e-3, fatol=1e-3, adaptive=True,
                                  initial_simplex=None))
        u = q.x
        c = cost(u)
        if c < best[0]:
            best = (c, u.copy(), state['b'])
    return best


def full_eval(cfg, u, b, NA):
    ng = len(cfg) - 1
    ts, gaps, Lo = unpack(u, ng)
    r = NA * Lo; half = max(6.5, r + 0.3)
    res = FC.metrics(cfg, ts, gaps, b, Lo, r, half, n=20, solve_focus=True)
    if res is None:
        return None
    b = b + res['dz']
    # 1-D focus polish on the Design-3 merit (mean + 0.3 max), as the original refine3 did with b free
    def fcost(bb):
        rr = FC.metrics(cfg, ts, gaps, bb, Lo, r, half, n=20)
        c = 1e6 if rr is None else rr['rms'].mean() + 0.3 * rr['rms'].max()
        if DEPTH and rr is not None:
            for d in (-1.0, 1.0):
                q = FC.metrics(cfg, ts, gaps, bb, Lo + d, r, half, n=12)
                c += 1e6 if q is None else LAM_D * 0.5 * (q['rms'].mean() + 0.3 * q['rms'].max())
        return c
    grid = b + np.arange(-0.4, 0.41, 0.05)
    cs = [fcost(x) for x in grid]
    b0 = grid[int(np.argmin(cs))]
    from scipy.optimize import minimize_scalar
    q = minimize_scalar(fcost, bounds=(b0 - 0.05, b0 + 0.05), method='bounded', options=dict(xatol=1e-3))
    b = q.x if q.fun <= min(cs) else b0
    res = FC.metrics(cfg, ts, gaps, b, Lo, r, half, n=20)
    mt, fnum = FC.mtf25(cfg, ts, gaps, b, Lo, r, half)
    light = (NA / SW.NA0) ** 2 * res['fr'].mean()
    dep = []
    for d in (-1.0, 1.0):
        q = FC.metrics(cfg, ts, gaps, b, Lo + d, r, half, n=16)
        dep.append((d, float(q['rms'].mean()), float(q['rms'].max())) if q is not None else (d, 1e3, 1e3))
    return dict(cfg=cfg, ts=float(ts), gaps=[float(g) for g in gaps], Lo=float(Lo), b=float(b), D=float(2 * r),
                half=float(half), eye_to_lens=float(Lo + FC.FILT_T + ts), NA_rel=float(NA / SW.NA0),
                light_rel=float(light), m=float(res['m']), rms=res['rms'].round(2).tolist(),
                rms_mean=float(res['rms'].mean()), rms_max=float(res['rms'].max()), vig=float(res['fr'].min()),
                xr=[float(res['c'][:, 0].min()), float(res['c'][:, 0].max())], mtf25_min=float(mt.min()),
                mtf25_mean=float(mt.mean()), fnum=float(fnum), mech=bool(res['mech']),
                depth=dep, track=float(Lo + FC.FILT_T + ts + sum(gaps) + sum(SW.EM[tuple(e)][1] for e in cfg) + b + FC.COVER_T + FC.COVER_GAP))


def meets(e):
    if e is not None and DEPTH and any(m_ > REF_D['mean'] or x_ > REF_D['max'] for _, m_, x_ in e['depth']):
        return False
    return (e is not None and e['rms_mean'] <= REF['mean'] and e['rms_max'] <= REF['max'] and e['vig'] >= REF['vig']
            and e['mtf25_min'] >= REF['mtf'] and e['mech'] and 0.529 <= e['m'] <= 0.591
            and e['xr'][0] >= 0.3 and e['xr'][1] <= 9.3)


def refine_job(row):
    cfg = [tuple(c) for c in row['cfg']]
    u0 = np.r_[SW.TS, row['gaps'], row['Lo']]
    c, u, b = optimise(cfg, u0, row['b'], SW.NA_SCREEN, iters=2, maxiter=300)
    e = full_eval(cfg, u, b, SW.NA_SCREEN) if c < 1e5 else None
    return dict(cfg=cfg, cost=float(c), u=u.tolist(), b=float(b), eval=e)


def ladder_job(row):
    cfg = [tuple(c) for c in row['cfg']]
    u, b = np.array(row['u']), row['b']
    best_ok = None; trail = []
    # go down first if the screening NA is not yet good enough, then up
    K0 = SW.NA_K
    ks = [round(K0 - 0.1 * i, 2) for i in range(5)] if not meets(row['eval']) else []
    start = K0
    for k in ks:
        c, u2, b2 = optimise(cfg, u, b, k * SW.NA0, iters=2, maxiter=300)
        e = full_eval(cfg, u2, b2, k * SW.NA0)
        trail.append((k, None if e is None else round(e['rms_mean'], 2), None if e is None else round(e['rms_max'], 2)))
        if meets(e):
            best_ok = e; u, b, start = u2, b2, k; break
    else:
        if not ks:
            best_ok = row['eval']
    if best_ok is None:
        return dict(cfg=cfg, best=None, trail=trail)
    k = start
    while k < 3.0:
        k = round(k + 0.1, 2)
        c, u2, b2 = optimise(cfg, u, b, k * SW.NA0, iters=2, maxiter=300)
        e = full_eval(cfg, u2, b2, k * SW.NA0)
        trail.append((k, None if e is None else round(e['rms_mean'], 2), None if e is None else round(e['rms_max'], 2)))
        if not meets(e):
            break
        best_ok, u, b = e, u2, b2
    best_ok['u'] = u.tolist() if hasattr(u, 'tolist') else list(u)
    return dict(cfg=cfg, best=best_ok, trail=trail)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "refine":
        tags = sys.argv[2].split(','); ntop = int(sys.argv[3])
        rows = []
        for t in tags:
            rr = json.load(open(f'../results/wide_screen_{t}.json'))
            rows += rr[:ntop]
        out = []
        with Pool(2) as p:
            for i, r in enumerate(p.imap_unordered(refine_job, rows)):
                out.append(r)
                e = r['eval']
                print(i, round(r['cost'], 2), r['cfg'], e and round(e['rms_mean'], 2), e and round(e['rms_max'], 2),
                      e and round(e['eye_to_lens'], 1), flush=True)
        out.sort(key=lambda r: r['cost'])
        json.dump(out, open(f'../results/wide_refined_{"_".join(tags)}.json', 'w'))
    elif mode == "ladder":
        src = sys.argv[2]; ntop = int(sys.argv[3])
        rows = [r for r in json.load(open(src)) if r['eval'] is not None][:ntop]
        out = []
        with Pool(2) as p:
            for r in p.imap_unordered(ladder_job, rows):
                out.append(r)
                b = r['best']
                print(r['cfg'], 'NO' if b is None else f"NA x{b['NA_rel']:.2f} light x{b['light_rel']:.2f} "
                      f"rms {b['rms_mean']:.2f}/{b['rms_max']:.2f} eye {b['eye_to_lens']:.1f} f/{b['fnum']:.1f}", r['trail'], flush=True)
        out.sort(key=lambda r: -(r['best']['light_rel'] if r['best'] else 0))
        json.dump(out, open(src.replace('.json', '_ladder.json'), 'w'), indent=1)
