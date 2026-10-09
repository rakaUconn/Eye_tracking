"""Multi-element builder (per-gap list) for the final stock design: filter at the stop, cover glass on the sensor."""
import numpy as np
from raytrace import Surf
import stock_final as SF
from stock import element
def build_multi(ts, gaps, b):
    gaps = np.atleast_1d(gaps)
    S = [Surf(0.0, kind="stop", ap=(SF.XC, 0, SF.SR)), Surf(0.0, np.inf, SF.FILT_G), Surf(SF.FILT_T, np.inf, "air")]
    z = SF.FILT_T + ts
    for k, (name, flip) in enumerate(SF.CFG):
        el, dia = element(name, flip)
        for R, t, med in el:
            S.append(Surf(z, R, med, ap=(0, 0, 0.45*dia))); z += t
        if k < len(SF.CFG)-1: z += gaps[min(k, len(gaps)-1)]
    zc = z + b
    S += [Surf(zc, np.inf, "N-BK7"), Surf(zc+SF.COVER_T, np.inf, "air")]
    return S, zc + SF.COVER_T + SF.COVER_GAP
