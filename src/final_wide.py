"""Stage 4: push NA for the shortlisted configurations with multi-start re-optimisation (step 0.05 in NA/NA0),
report why the next step fails.  -> ../results/wide_final.json"""
import json, sys, numpy as np
from multiprocessing import Pool
import refine_wide as RW, search_wide as SW


def why(e):
    if e is None: return ['trace']
    R = RW.REF; w = []
    if e['rms_mean'] > R['mean']: w.append('mean')
    if e['rms_max'] > R['max']: w.append('max')
    if e['vig'] < R['vig']: w.append('vig')
    if e['mtf25_min'] < R['mtf']: w.append('mtf')
    if not e['mech']: w.append('mech')
    if RW.DEPTH and any(m_ > RW.REF_D['mean'] or x_ > RW.REF_D['max'] for _, m_, x_ in e['depth']): w.append('depth')
    if not 0.529 <= e['m'] <= 0.591: w.append('m')
    if e['xr'][0] < 0.3 or e['xr'][1] > 9.3: w.append('x')
    return w


def multistart(cfg, u, b, k, nstart=3 if RW.DEPTH else 4):
    rng = np.random.default_rng(int(k * 100))
    ng = len(cfg) - 1
    best = None
    for s in range(nstart):
        u0 = np.array(u, float)
        if s:
            u0 = u0 + np.r_[0.5, np.full(ng, 3.0), 4.0] * rng.normal(size=ng + 2)
            u0[0] = max(0.3, u0[0])
        c, u2, b2 = RW.optimise(cfg, u0, b, k * SW.NA0, iters=2 if RW.DEPTH else 3, maxiter=300 if RW.DEPTH else 400)
        if c >= 1e5: continue
        e = RW.full_eval(cfg, u2, b2, k * SW.NA0)
        ok = RW.meets(e)
        key = (ok, -c)
        if best is None or key > best[0]:
            best = (key, e, u2, b2)
    return best


def job(item):
    cfg, u, b, k0 = item
    cfg = [tuple(c) for c in cfg]
    best_ok = None; log = []
    k = k0
    fails = 0
    while k <= 2.2 and fails < 2:
        r = multistart(cfg, u, b, k)
        if r is None:
            fails += 1; log.append((k, 'none')); k = round(k + 0.05, 2); continue
        (ok, _), e, u2, b2 = r
        log.append((k, round(e['rms_mean'], 2), round(e['rms_max'], 2), round(e['vig'], 3), round(e['mtf25_min'], 3), why(e)))
        if ok:
            e['u'] = u2.tolist(); best_ok = e; u, b = u2, b2; fails = 0
        else:
            fails += 1
        k = round(k + 0.05, 2)
    return dict(cfg=cfg, best=best_ok, log=log)


if __name__ == "__main__":
    items = []
    for f in ('../results/wide_refined_23_ladder.json', '../results/wide_refined_4_ladder.json'):
        rows = [r for r in json.load(open(f)) if r['best']]
        for r in rows[:int(sys.argv[1]) if len(sys.argv) > 1 else 4]:
            b = r['best']
            items.append((r['cfg'], b['u'], b['b'], 1.0 if RW.DEPTH else round(b['NA_rel'], 2)))
    if RW.DEPTH:
        P = json.load(open('../results/design3_final.json'))
        items.append((P['cfg'], [P['ts']] + list(P['gap']) + [P['Lo']], P['b'], 1.0))
    out = []
    with Pool(2) as p:
        for r in p.imap_unordered(job, items):
            out.append(r); b = r['best']
            print([c[0] + ('r' if c[1] else '') for c in r['cfg']],
                  None if b is None else f"NA x{b['NA_rel']:.2f} light/D3 {b['light_rel']/0.9364:.2f} rms {b['rms_mean']:.2f}/{b['rms_max']:.2f} mtf {b['mtf25_min']:.3f} vig {b['vig']:.2f} eye {b['eye_to_lens']:.1f} D {b['D']:.1f}",
                  r['log'], flush=True)
    out.sort(key=lambda r: -(r['best']['light_rel'] if r['best'] else 0))
    json.dump(out, open('../results/wide_final%s.json' % ('_depth' if RW.DEPTH else ''), 'w'), indent=1)
