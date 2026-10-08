"""Navarro (1999) relaxed eye, conic surfaces, P1/P4 Purkinje images vs gaze (Part A)."""
import numpy as np
# (R, k, z_vertex, n_after)  eye frame: z into the eye, apex at 0.  lambda=0.85 um indices (approx, Navarro dispersion)
def indices(wl):
    # Navarro dispersion model n = n0 + a/(...) simplified: use 555nm values minus small NIR drop
    d = {0.555: (1.3777, 1.3391, 1.4222, 1.3391), 0.85: (1.3718, 1.3331, 1.4130, 1.3331)}
    return d[wl]
def surfaces(wl=0.85):
    nc, na, nl, nv = indices(wl)
    return [dict(R=7.72, k=-0.26, z=0.0,   n_before=1.0, n_after=nc),
            dict(R=6.50, k=0.0,  z=0.55,  n_before=nc,  n_after=na),
            dict(R=10.2, k=-3.1316, z=4.10-0.0, n_before=na, n_after=nl),   # lens front (3.05 aq) -> z=3.60? see below
            dict(R=-6.0, k=-1.0, z=7.60+0.0, n_before=nl, n_after=nv)]
# Navarro: cornea 0.55, aqueous 3.05 -> lens front at 3.60, lens 4.0 -> back at 7.60
def surfaces(wl=0.85):
    nc, na, nl, nv = indices(wl)
    return [dict(R=7.72, k=-0.26, z=0.0,  n_before=1.0, n_after=nc),
            dict(R=6.50, k=0.0,  z=0.55, n_before=nc,  n_after=na),
            dict(R=10.2, k=-3.1316, z=3.60, n_before=na, n_after=nl),
            dict(R=-6.0, k=-1.0, z=7.60, n_before=nl, n_after=nv)]

def intersect(P, D, s):
    """ray/conic-surface intersection (nearest root of exact conic); returns point, unit normal pointing along +z side?"""
    R, k, zv = s["R"], s["k"], s["z"]; c = 1.0/R
    # F(x,y,z)= c(x²+y²+(1+k)(z-zv)²) - 2(z-zv)=0  (vertex at zv, centre on +z side for R>0)
    Dx, Dy, Dz = D[:, 0], D[:, 1], D[:, 2]
    px, py, pz = P[:, 0], P[:, 1], P[:, 2]-zv
    a = c*(Dx**2 + Dy**2 + (1+k)*Dz**2)
    b = 2*c*(px*Dx + py*Dy + (1+k)*pz*Dz) - 2*Dz
    cc = c*(px**2 + py**2 + (1+k)*pz**2) - 2*pz
    t = np.full(len(P), np.nan)
    lin = np.abs(a) < 1e-12
    t[lin] = -cc[lin]/b[lin]
    disc = b*b - 4*a*cc
    ok = (~lin) & (disc >= 0)
    sq = np.sqrt(np.where(ok, disc, 0))
    t1 = (-b - sq)/(2*np.where(lin, 1, a)); t2 = (-b + sq)/(2*np.where(lin, 1, a))
    # choose the root closest to the vertex plane crossing (the physical branch, |sag| small)
    tv = (zv - P[:, 2])/D[:, 2]
    pick = np.where(np.abs(t1 - tv) < np.abs(t2 - tv), t1, t2)
    t = np.where(ok, pick, t)
    Q = P + t[:, None]*D
    q = Q.copy(); q[:, 2] -= zv
    N = np.column_stack([c*q[:, 0], c*q[:, 1], c*(1+k)*q[:, 2] - 1.0])
    N /= np.linalg.norm(N, axis=1)[:, None]
    return Q, N

def refract(D, N, n1, n2):
    cosi = -np.einsum('ij,ij->i', N, D)
    N = np.where(cosi[:, None] < 0, -N, N); cosi = np.abs(cosi)
    r = n1/n2; kk = 1 - r*r*(1-cosi**2)
    D2 = r*D + (r*cosi - np.sqrt(np.maximum(kk, 0)))[:, None]*N
    return D2/np.linalg.norm(D2, axis=1)[:, None], kk >= 0
def reflect(D, N):
    return D - 2*np.einsum('ij,ij->i', D, N)[:, None]*N

def purkinje(which, d_in, wl=0.85, patch=4.0, n=301):
    """d_in: unit direction (eye frame) of the incoming parallel light. Returns Q-points and outgoing rays (P,D)."""
    S = surfaces(wl)
    # launch grid in a plane perpendicular to d_in, centred on the apex-ish
    d = d_in/np.linalg.norm(d_in)
    e1 = np.cross(d, [0, 1, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
    g = np.linspace(-patch, patch, n); X, Y = np.meshgrid(g, g); m = X**2+Y**2 <= patch**2
    P = -d*30 + X[m, None]*e1 + Y[m, None]*e2 + np.array([0, 0, 3.0])
    D = np.tile(d, (len(P), 1))
    alive = np.ones(len(P), bool)
    if which == 1:
        Q, N = intersect(P, D, S[0]); D = reflect(D, N); return Q, D, alive
    # P4: refract through 0,1,2, reflect at 3, back through 2,1,0
    order = [(0, 1), (1, 1), (2, 1), (3, 0), (2, -1), (1, -1), (0, -1)]
    for idx, (si, fwd) in enumerate(order):
        s = S[si]; Q, N = intersect(P, D, s)
        if si == 3 and fwd == 0:
            D = reflect(D, N); P = Q; continue
        n1, n2 = (s["n_before"], s["n_after"]) if fwd == 1 else (s["n_after"], s["n_before"])
        D, ok = refract(D, N, n1, n2); alive &= ok; P = Q
    return P, D, alive

def image_point(P, D, alive, cam, stop_r=3.125, stop_c=None, stop_z=None):
    """Least-squares virtual image point of the rays that pass through the camera stop.
    cam = camera stop centre (3,), camera looks along -z of its frame -> stop plane z = cam[2]."""
    t = (cam[2] - P[:, 2])/D[:, 2]
    X = P + t[:, None]*D
    sel = alive & (t > 0) & ((X[:, 0]-cam[0])**2 + (X[:, 1]-cam[1])**2 <= stop_r**2)
    if sel.sum() < 5: return None, 0
    Pp, Dd = P[sel], D[sel]
    A = np.zeros((3, 3)); b = np.zeros(3)
    for p, d in zip(Pp, Dd):
        M = np.eye(3) - np.outer(d, d); A += M; b += M@p
    return np.linalg.solve(A, b), sel.sum()

def rot_y(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rot_x(a):
    c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def glints(theta_x_deg, theta_y_deg, beta_deg=17.0, Lcam=141.0, COR=13.5, wl=0.85, stop_r=3.125):
    """Lab frame origin at eye centre of rotation, camera on -z looking +z... eye faces -z at gaze 0.
    Source direction (to source) in lab: rotated beta about y from the -z axis. Returns lab positions of P1,P4 (virtual images)."""
    R = rot_x(np.radians(theta_x_deg)) @ rot_y(np.radians(theta_y_deg))   # eye->lab rotation
    # eye frame has +z into the eye (away from camera at gaze 0): lab z_lab = -(z_e - COR) at theta=0 -> flip
    F = np.eye(3)
    to_lab = lambda pe: (R @ (F @ (pe - np.array([0, 0, COR])).T)).T if pe.ndim > 1 else R @ (F @ (pe - np.array([0, 0, COR])))
    # lab -> eye
    def dir_to_eye(dl): return F @ (R.T @ dl)
    u_src = np.array([np.sin(np.radians(beta_deg)), 0, -np.cos(np.radians(beta_deg))])  # towards source
    d_in = dir_to_eye(-u_src)       # light travel direction in eye frame
    cam_lab = np.array([0, 0, -(Lcam + COR)])
    cam_e = F @ (R.T @ cam_lab) + np.array([0, 0, COR])
    out = {}
    for w in (1, 4):
        P, D, al = purkinje(w, d_in, wl)
        # camera stop plane perpendicular to the lab axis -> do the stop test in lab frame
        Pl = np.array([to_lab(p) for p in P]); Dl = (R @ (F @ D.T)).T
        pt, ns = image_point(Pl, Dl, al, cam_lab, stop_r)
        out[w] = (pt, ns)
    return out
