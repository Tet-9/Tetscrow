"""Tiny ray-marching renderer (numpy only) used to pre-render the Tet hawk mascot as soft 3D stills."""
from PIL import Image
import math
import numpy as np

F = np.float32
def L(v): return np.sqrt((v * v).sum(-1))
def nrm(v): return v / np.maximum(L(v)[..., None], 1e-9)
def V(*a): return np.array(a, F)
def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def mix(a, b, t): return a + (b - a) * (t[..., None] if np.ndim(t) else t)
def hexc(h):
    h = h.lstrip('#')
    return (np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], F)) ** 2.2

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)

def rx(a): c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], F)
def ry(a): c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], F)
def rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], F)
def loc(p, c, R=None):
    q = p - c
    return q if R is None else q @ R

def sph(p, c, r): return L(p - c) - r
def ell(p, c, r, R=None):
    q = loc(p, c, R) / r
    k0 = L(q); k1 = L(q / r)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-6)
def tcap(p, a, b, r1, r2):
    pa = p - a; ba = b - a
    h = np.clip((pa * ba).sum(-1) / (ba * ba).sum(), 0, 1)
    return L(pa - ba * h[:, None]) - (r1 + (r2 - r1) * h)
def box(p, c, b, r=0.0, R=None):
    q = np.abs(loc(p, c, R)) - b + r
    return L(np.maximum(q, 0)) + np.minimum(q.max(-1), 0) - r
def cyl(p, c, r, h, rr=0.0, R=None):
    q = loc(p, c, R)
    d0 = L(q[:, [0, 2]]) - r + rr; d1 = np.abs(q[:, 1]) - h + rr
    return np.minimum(np.maximum(d0, d1), 0) + L(np.stack([np.maximum(d0, 0), np.maximum(d1, 0)], -1)) - rr
def torz(p, c, R_, r, R=None):
    q = loc(p, c, R)
    return L(np.stack([L(q[:, :2]) - R_, q[:, 2]], -1)) - r
def tory(p, c, R_, r, R=None):
    q = loc(p, c, R)
    return L(np.stack([L(q[:, [0, 2]]) - R_, q[:, 1]], -1)) - r

def _h(p):
    return np.abs(np.modf(np.sin((p * V(127.1, 311.7, 74.7)).sum(-1)) * 43758.5453)[0]).astype(F)
def vnoise(p):
    i = np.floor(p); f = p - i; f = f * f * (3 - 2 * f)
    o = lambda a, b, c: _h(i + V(a, b, c))
    x00 = o(0, 0, 0) * (1 - f[:, 0]) + o(1, 0, 0) * f[:, 0]; x10 = o(0, 1, 0) * (1 - f[:, 0]) + o(1, 1, 0) * f[:, 0]
    x01 = o(0, 0, 1) * (1 - f[:, 0]) + o(1, 0, 1) * f[:, 0]; x11 = o(0, 1, 1) * (1 - f[:, 0]) + o(1, 1, 1) * f[:, 0]
    return (x00 * (1 - f[:, 1]) + x10 * f[:, 1]) * (1 - f[:, 2]) + (x01 * (1 - f[:, 1]) + x11 * f[:, 1]) * f[:, 2]


class Scene:
    """parts(p)->{name: dist}; combine(dists)->trace distance; mat(name,p)->(color, spec, gloss, refl, emis)."""
    def __init__(self, parts, combine, mat, bound, ground=None):
        self.parts, self.combine, self.mat, self.bound, self.ground = parts, combine, mat, bound, ground
    def sdf(self, p): return self.combine(self.parts(p))


def render(sc, W, H, cam_pos, target, fov=24, ss=2, light=(-0.55, 0.8, 0.65), shadow_ground=True, tau=0.05, exposure=1.0):
    w, h = W * ss, H * ss
    cam_pos = V(*cam_pos); target = V(*target)
    fw = nrm(target - cam_pos); rt = nrm(np.cross(fw, V(0, 1, 0))); up = np.cross(rt, fw)
    ys, xs = np.mgrid[0:h, 0:w].astype(F)
    u = ((xs + 0.5) / w * 2 - 1) * (W / H) * math.tan(math.radians(fov) / 2)
    v = (1 - (ys + 0.5) / h * 2) * math.tan(math.radians(fov) / 2)
    rd = nrm(fw[None, :] + u.reshape(-1, 1) * rt + v.reshape(-1, 1) * up)
    N = rd.shape[0]
    ro = np.broadcast_to(cam_pos, (N, 3))
    bc, br = V(*sc.bound[0]), sc.bound[1]
    oc = ro - bc
    b = (oc * rd).sum(-1); c = (oc * oc).sum(-1) - br * br; disc = b * b - c
    inb = disc > 0
    sq = np.sqrt(np.maximum(disc, 0))
    t = np.where(inb, -b - sq, 0).astype(F); tmax = np.where(inb, -b + sq, 0).astype(F)
    alive = np.nonzero(inb)[0]; hit = np.zeros(N, bool)
    for _ in range(140):
        if alive.size == 0: break
        p = ro[alive] + rd[alive] * t[alive, None]
        d = sc.sdf(p); tt = t[alive]
        hh = d < 0.0009 * np.maximum(tt, 1)
        hit[alive[hh]] = True
        t[alive] = tt + d * 0.85
        alive = alive[~(hh | (t[alive] > tmax[alive]))]
    idx = np.nonzero(hit)[0]
    rgb = np.zeros((N, 3), F); alpha = np.zeros(N, F)
    lt = nrm(V(*light)[None, :])[0]
    def shadow(p, ld, k=9.0, steps=26):
        res = np.ones(p.shape[0], F); tt = np.full(p.shape[0], 0.06, F)
        for _ in range(steps):
            d = sc.sdf(p + ld * tt[:, None]); res = np.minimum(res, k * d / tt); tt = tt + np.clip(d, 0.04, 0.5)
        return np.clip(res, 0, 1)
    if idx.size:
        p = ro[idx] + rd[idx] * t[idx, None]; e = 0.003
        ks = [V(1, -1, -1), V(-1, -1, 1), V(-1, 1, -1), V(1, 1, 1)]
        n = nrm(sum(k * sc.sdf(p + k * e)[:, None] for k in ks))
        v_ = -rd[idx]
        ao = np.ones(idx.size, F)
        for i in range(1, 5):
            hh_ = 0.06 * i; ao -= (hh_ - np.minimum(sc.sdf(p + n * hh_), hh_)) * (0.9 / i) * 1.6
        ao = np.clip(ao, 0.15, 1)
        sh = shadow(p + n * 0.02, lt)
        # material blend
        dd = sc.parts(p); names = list(dd.keys()); D = np.stack([dd[k] for k in names], 0)
        wgt = np.exp(-(D - D.min(0)) / tau); wgt /= wgt.sum(0)
        col = np.zeros((idx.size, 3), F); spec = np.zeros(idx.size, F); gloss = np.zeros(idx.size, F); refl = np.zeros(idx.size, F); em = np.zeros((idx.size, 3), F)
        for k, name in enumerate(names):
            m = wgt[k] > 0.02
            if not m.any(): continue
            c_, s_, g_, r_, e_ = sc.mat(name, p[m])
            wm = wgt[k][m]
            col[m] += c_ * wm[:, None]; spec[m] += s_ * wm; gloss[m] += g_ * wm; refl[m] += r_ * wm; em[m] += e_ * wm[:, None]
        def lam(ld, wrap): return np.clip(((n * ld).sum(-1) + wrap) / (1 + wrap), 0, 1)
        key = V(1.0, 0.92, 0.8) * 2.15; fill_d = nrm(V(0.8, 0.1, 0.55)[None, :])[0]; rim_d = nrm(V(0.25, 0.55, -0.85)[None, :])[0]
        fres = (1 - np.clip((n * v_).sum(-1), 0, 1)) ** 3
        skyc = V(0.62, 0.55, 0.9) * 0.55; grdc = V(0.42, 0.3, 0.5) * 0.28
        amb = mix(np.broadcast_to(grdc, (idx.size, 3)), np.broadcast_to(skyc, (idx.size, 3)), n[:, 1] * 0.5 + 0.5)
        lit = (lam(lt, 0.4) * sh)[:, None] * key + lam(fill_d, 0.5)[:, None] * V(0.55, 0.5, 0.95) * 0.85 + amb * ao[:, None]
        lit = lit + (lam(rim_d, 0.2) * fres)[:, None] * V(0.85, 0.75, 1.0) * 2.4
        col_ = col * lit * (0.5 + 0.5 * ao[:, None])
        hv = nrm(lt[None, :] + v_)
        sp = (np.clip((n * hv).sum(-1), 0, 1) ** np.maximum(gloss, 1)) * spec * sh
        rr = 2 * (n * v_).sum(-1)[:, None] * n - v_
        env = mix(np.broadcast_to(V(0.10, 0.07, 0.16), rr.shape), np.broadcast_to(V(0.85, 0.8, 1.0), rr.shape), np.clip(rr[:, 1] * 0.5 + 0.55, 0, 1)) 
        box_ = np.clip((rr * lt).sum(-1), 0, 1) ** 50 * 3.0
        refl_c = (env * 0.6 + box_[:, None]) * (refl * (0.35 + 0.65 * fres))[:, None]
        out = col_ + sp[:, None] * V(1, 0.96, 0.9) * 1.6 + refl_c + em
        rgb[idx] = out; alpha[idx] = 1
    if shadow_ground and sc.ground is not None:
        gy = sc.ground; ng = np.nonzero((~hit) & (rd[:, 1] < -1e-4))[0]
        tg = (gy - ro[ng, 1]) / rd[ng, 1]; pg = ro[ng] + rd[ng] * tg[:, None]
        near = (pg[:, 0] ** 2 + pg[:, 2] ** 2) < 30
        ng = ng[near]; pg = pg[near]
        if ng.size:
            s2 = shadow(pg + V(0, 0.02, 0), lt, 6.0, 30); dg = np.maximum(sc.sdf(pg), 0)
            dark = np.clip((1 - s2) * 0.55 + np.exp(-dg * 2.6) * 0.6, 0, 0.85)
            dark *= np.exp(-((pg[:, 0] ** 2 + pg[:, 2] ** 2) / 22.0))
            rgb[ng] = V(0.02, 0.0, 0.06); alpha[ng] = dark
    rgb = 1 - np.exp(-rgb * exposure); rgb = np.clip(rgb, 0, 1) ** (1 / 2.2)
    pm = rgb * alpha[:, None]
    pm = pm.reshape(h, w, 3); al = alpha.reshape(h, w)
    pm = pm.reshape(H, ss, W, ss, 3).mean((1, 3)); al = al.reshape(H, ss, W, ss).mean((1, 3))
    outc = np.where(al[..., None] > 1e-4, pm / np.maximum(al[..., None], 1e-4), 0)
    img = np.dstack([np.clip(outc, 0, 1) * 255, np.clip(al, 0, 1) * 255]).astype(np.uint8)
    
    return Image.fromarray(img, "RGBA")
