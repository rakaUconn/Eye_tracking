"""Minimal 3-D sequential ray tracer (spherical surfaces, apertures, planar mirrors)
and glass catalogue (Sellmeier) used for the single-sensor binocular eye tracker study."""
import numpy as np

# Sellmeier (B1,B2,B3,C1,C2,C3[um^2]) - Schott catalogue values
GLASS = {
    "N-BK7": (1.03961212, 0.231792344, 1.01046945, 0.00600069867, 0.0200179144, 103.560653),
    "F2":    (1.34533359, 0.209073176, 0.937357162, 0.00997743871, 0.0470450767, 111.886764),
    "N-SF5": (1.52481889, 0.187085527, 1.42729015, 0.011254756, 0.0588995392, 129.141675),
    "N-BAF10": (1.5851495, 0.143559385, 1.08521269, 0.00926681282, 0.0424489805, 105.613573),
    "N-SF10": (1.62153902, 0.256287842, 1.64447552, 0.0122241457, 0.0595736775, 147.468793),
    "N-LAK22": (1.14229781, 0.535138441, 1.04088385, 0.00585778594, 0.0198546147, 100.834017),
    "SF5": (1.46141885, 0.247713019, 0.949995832, 0.011137445, 0.0508594669, 112.041888),
    "N-SF6": (1.77931763, 0.338149866, 2.08734474, 0.0133714182, 0.0617533621, 174.01759),
}

def index(name, wl_um):
    if name == "air":
        return 1.0
    B1, B2, B3, C1, C2, C3 = GLASS[name]
    l2 = wl_um**2
    return np.sqrt(1 + B1*l2/(l2-C1) + B2*l2/(l2-C2) + B3*l2/(l2-C3))

class Surf:
    """Spherical surface; vertex at (x0, 0, z). R=inf -> plane. after = medium behind surface.
    ap = (cx, cy, radius) clear aperture (rays outside are vignetted)."""
    def __init__(self, z, R=np.inf, after="air", x0=0.0, ap=None, kind="refract"):
        self.z, self.R, self.after, self.x0, self.ap, self.kind = z, R, after, x0, ap, kind

def trace(P, D, surfs, wl, n0=1.0):
    """P,D: (N,3) positions/unit directions. Returns P,D,alive at last surface."""
    P, D = P.copy(), D.copy()
    alive = np.ones(len(P), bool)
    n = n0
    for s in surfs:
        if np.isinf(s.R):
            t = (s.z - P[:, 2]) / D[:, 2]
            Q = P + t[:, None]*D
            N = np.tile([0, 0, -1.0], (len(P), 1))
        else:
            C = np.array([s.x0, 0, s.z + s.R])
            oc = P - C
            b = np.einsum('ij,ij->i', oc, D)
            c = np.einsum('ij,ij->i', oc, oc) - s.R**2
            disc = b*b - c
            alive &= disc >= 0
            sq = np.sqrt(np.maximum(disc, 0))
            t = -b - np.sign(s.R)*sq
            Q = P + t[:, None]*D
            N = (Q - C)/s.R
        if s.ap is not None:
            alive &= (Q[:, 0]-s.ap[0])**2 + (Q[:, 1]-s.ap[1])**2 <= s.ap[2]**2
        if s.kind == "stop":
            P = Q
            continue
        if s.kind == "mirror":
            D = D - 2*np.einsum('ij,ij->i', D, N)[:, None]*N
            P = Q
            continue
        n2 = index(s.after, wl)
        # orient normal against ray
        cosi = -np.einsum('ij,ij->i', N, D)
        N = np.where(cosi[:, None] < 0, -N, N)
        cosi = np.abs(cosi)
        r = n/n2
        k = 1 - r*r*(1 - cosi**2)
        alive &= k >= 0
        D = r*D + (r*cosi - np.sqrt(np.maximum(k, 0)))[:, None]*N
        D /= np.linalg.norm(D, axis=1)[:, None]
        P, n = Q, n2
    return P, D, alive

def to_plane(P, D, z):
    t = (z - P[:, 2])/D[:, 2]
    return P + t[:, None]*D
