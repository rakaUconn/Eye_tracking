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
 "LE1104":     (150., 25.4, [(49.1, 3.1, "air"), (131.6, 0, None)]),
 "LBF254-100": (100., 25.4, [(60.02, 4.0, "air"), (-353.3, 0, None)]),
 "LBF254-200": (200., 25.4, [(121.5, 4.0, "air"), (-684.5, 0, None)]),
 "LA1979":     (199.3, 50.8, [(inf, 6.2, "air"), (-103.0, 0, None)]),
 "LB1294":     (175.0, 25.4, [(179.8, 2.9, "air"), (-179.8, 0, None)]),
 "LB1199":     (200.0, 50.8, [(205.0, 6.2, "air"), (-205.0, 0, None)]),
 "LE1015":     (200.0, 50.8, [(65.2, 6.2, "air"), (171.6, 0, None)]),
 "LC1120":     (-99.6, 25.4, [(inf, 4.0, "air"), (51.5, 0, None)]),
 "LC1715":     (-49.8, 25.4, [(inf, 3.5, "air"), (25.7, 0, None)]),
 "LD1613":     (-100.0, 25.4, [(-103.7, 4.0, "air"), (103.7, 0, None)]),
 "LD1464":     (-50.0, 25.4, [(-52.0, 3.0, "air"), (52.0, 0, None)]),
 "LF1822":     (-100.0, 25.4, [(100.0, 3.0, "air"), (33.7, 0, None)]),
 "LF1097":     (-200.0, 25.4, [(100.0, 3.0, "air"), (50.2, 0, None)]),
 "LA1229":     (174.4, 25.4, [(inf, 2.9, "air"), (-90.1, 0, None)]),
 # added for the wide search (search_wide.py)
 "LC1611":     (-149.4, 50.8, [(inf, 4.0, "air"), (77.2, 0, None)]),
 "LD1170":     (-75.0, 25.4, [(-77.9, 3.5, "air"), (77.9, 0, None)]),
 "LF1988":     (-500.0, 25.4, [(250.0, 3.0, "air"), (126.3, 0, None)]),
}
# first-glass assignment: doublets: crown N-BAF10/N-BK7 first then flint; fix media after each surface
GL = {"AC254-050": ("N-BAF10", "N-SF10"), "AC254-075-B": ("N-BAF10", "N-SF6"), "AC254-150": ("N-BK7", "SF5"),
      "AC508-150-B": ("N-LAK22", "N-SF6"), "LBF254-050": ("N-BK7",), "LB1471": ("N-BK7",), "LA1131": ("N-BK7",), "LE1234": ("N-BK7",), "LE1104": ("N-BK7",), "LBF254-100": ("N-BK7",), "LBF254-200": ("N-BK7",), "LA1229": ("N-BK7",), "LA1979": ("N-BK7",), "LB1294": ("N-BK7",), "LB1199": ("N-BK7",), "LE1015": ("N-BK7",), "LC1120": ("N-BK7",), "LC1715": ("N-BK7",), "LD1613": ("N-BK7",), "LD1464": ("N-BK7",), "LF1822": ("N-BK7",), "LF1097": ("N-BK7",), "LC1611": ("N-BK7",), "LD1170": ("N-BK7",), "LF1988": ("N-BK7",)}
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
