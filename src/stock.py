"""Thorlabs stock lens library (from Thorlabs_Stock_Lens_Reference.md). Each element: list of
(R, thickness_to_next_surface, medium_after). Doublet crown/flint thickness SPLIT is an assumption
(total centre thickness is catalogue). N-SF6HT modelled as N-SF6, SF5 as Schott SF5 (verify vs .zmx)."""
import numpy as np
from raytrace import index
inf = np.inf
LIB = {  # name: (EFL, diameter, surfaces)
 "AC254-050":  (50.2, 25.4, [(33.3, 9.0, "N-SF10"), (-22.3, 2.5, "air"), (-291.1, 0, None)]),
 "AC254-075-B":(75.0, 25.4, [(36.90, 4.5, "N-SF6"), (-42.17, 2.1, "air"), (417.8, 0, None)]),
 "AC254-150":  (150.0, 25.4, [(91.6, 5.4, "SF5"), (-66.7, 2.5, "air"), (-197.7, 0, None)]),
 "AC508-150-B":(150.0, 50.8, [(112.2, 10.0, "N-SF6"), (-95.9, 3.2, "air"), (-325.1, 0, None)]),
 "LBF254-050": (50.0, 25.4, [(30.06, 6.5, "air"), (-172.0, 0, None)]),
 "LB1471":     (50.0, 25.4, [(50.6, 5.2, "air"), (-50.6, 0, None)]),
 "LA1131":     (49.8, 25.4, [(inf, 5.3, "air"), (-25.8, 0, None)]),
 "LE1234":     (100., 25.4, [(32.1, 3.6, "air"), (82.2, 0, None)]),
}
# first-glass assignment: doublets: crown N-BAF10/N-BK7 first then flint; fix media after each surface
GL = {"AC254-050": ("N-BAF10", "N-SF10"), "AC254-075-B": ("N-BAF10", "N-SF6"), "AC254-150": ("N-BK7", "SF5"),
      "AC508-150-B": ("N-LAK22", "N-SF6"), "LBF254-050": ("N-BK7",), "LB1471": ("N-BK7",), "LA1131": ("N-BK7",), "LE1234": ("N-BK7",)}
def element(name, flip=False):
    efl, dia, S = LIB[name]; gl = GL[name]
    R = [s[0] for s in S]; t = [s[1] for s in S]
    # media after surfaces: lens glasses in order, then air
    med = list(gl) + ["air"]
    if not flip:
        return [(R[i], t[i], med[i]) for i in range(len(R))], dia
    # reversed: radii negate/reverse, thicknesses reversed, media reversed
    Rr = [-r for r in R[::-1]]; tr = t[:-1][::-1] + [0]
    medr = list(gl[::-1]) + ["air"]
    return [(Rr[i], tr[i], medr[i]) for i in range(len(Rr))], dia
def efl_check(name, wl=0.5876):
    S, _ = element(name)
    M = np.eye(2); n = 1.0
    for R, t, med in S:
        n2 = index(med, wl); P = (n2-n)/R if np.isfinite(R) else 0.0
        M = np.array([[1, 0], [-P, 1]]) @ M          # refraction (y,nu)
        M = np.array([[1, t/n2], [0, 1]]) @ M if t else M; n = n2
    return -1/M[1, 0] if False else 1.0/(-M[1, 0])
if __name__ == "__main__":
    for k in LIB: print(k, "catalogue EFL", LIB[k][0], "computed", round(efl_check(k), 1))
