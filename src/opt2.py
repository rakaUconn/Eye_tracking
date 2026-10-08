import numpy as np, json, sys
from scipy.optimize import minimize
from raytrace import Surf, trace, to_plane
from channel import fields, rays_from, WLS, FILT_T, COVER_T
M_T=0.55; EX,EY=11.6,15.2; XC=-6.5
F5=fields(n=3,ex=EX,ey=EY,xc=XC)
T1,T2=6.0,2.5      # doublet crown / flint centre thicknesses (25 mm-class stock doublets)

def build(x, g):
    R=x[:6]; ts,gap=x[6],x[7]
    S=[]; z=ts
    for k in range(2):
        S.append(Surf(z,R[3*k],g[2*k],ap=(0,0,12.0))); z+=T1
        S.append(Surf(z,R[3*k+1],g[2*k+1],ap=(0,0,12.0))); z+=T2
        S.append(Surf(z,R[3*k+2],"air",ap=(0,0,12.0)))
        if k==0: z+=gap
    return S,z
def run(x,g,Lo,zoff,wl,F,stop_r=3.125,n=10):
    S,zl=build(x,g)
    pl=lambda z0:[Surf(z0,np.inf,"N-BK7"),Surf(z0+FILT_T,np.inf,"air"),Surf(z0+FILT_T+.5,np.inf,"N-BK7"),Surf(z0+FILT_T+.5+COVER_T,np.inf,"air")]
    out=[]
    for f in F:
        P,D=rays_from(f,Lo,XC,stop_r,n); P0=to_plane(P,D,0.0)
        Pn,Dn,a=trace(P0,D,S,wl); Pn,Dn,a2=trace(Pn,Dn,pl(zl),wl)
        Q=to_plane(Pn,Dn,zl+FILT_T+.5+COVER_T+zoff); out.append(Q[a&a2][:,:2])
    return out
def metrics(x,g,Lo,zoff,F=F5,wls=WLS,n=10):
    sp=[run(x,g,Lo,zoff,w,F,n=n) for w in wls]
    rms=[];c=[]
    for i in range(len(F)):
        pts=[sp[k][i] for k in range(len(wls))]
        if any(len(a)<15 for a in pts): return None
        cc=pts[1].mean(0); c.append(cc); a=np.vstack(pts)-cc; rms.append(np.sqrt((a**2).sum(1).mean()))
    c=np.array(c); m=abs((c[3,0]-c[5,0])/EX+(c[1,1]-c[7,1])/EY)/2
    return np.array(rms),c,m
def cost(v,g):
    x=v[:8]; Lo=v[8]; zoff=v[9]
    if not(0<=x[6]<=25 and 0<=x[7]<=30 and 135<=Lo<=150 and 20<=zoff<=90 and min(abs(x[:6]))>=20): return 1e6
    try: r=metrics(x,g,Lo,zoff)
    except Exception: return 1e6
    if r is None: return 1e6
    rms,c,m=r
    return (rms*1e3).mean()+0.3*rms.max()*1e3+2000*abs(m-M_T)
if __name__=="__main__":
    g=("N-BK7","F2","N-BK7","F2")
    best=None
    # start: two f~100 doublets, near-symmetric
    for sc in (1.0,):
        v0=[60,-43,-240, 240,43,-60, 6,5,141,40]
        v=np.array(v0,float)
        for it in range(6):
            r=minimize(cost,v,args=(g,),method="Nelder-Mead",options=dict(maxiter=600,xatol=1e-3,fatol=1e-4,adaptive=True))
            v=r.x; print(it,round(r.fun,2),np.round(v,2),flush=True)
        json.dump(dict(glass=g,v=list(v),cost=r.fun),open("../results/two_doublet.json","w"),indent=1)
