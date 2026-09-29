from sdf import *
from hawk import make_hawk, C

def K(c, spec=0.2, gloss=30, refl=0.05):
    def f(p):
        n = p.shape[0]; return np.broadcast_to(c, (n, 3)).copy(), spec, gloss, refl, np.zeros((n, 3), F)
    return f

def compose(hawk, props, bound, ground=-1.42):
    hp, hc, hm = hawk
    plist = props
    def parts(p):
        d = hp(p)
        for pp in plist: d.update(pp[0](p))
        return d
    def combine(d):
        o = hc(d)
        for pp in plist: o = np.minimum(o, pp[1](d))
        return o
    def mat(name, p):
        for pp in plist:
            if name in pp[3]: return pp[2][name](p)
        return hm(name, p)
    return Scene(parts, combine, mat, bound, ground)

def prop(fn_parts, fn_combine, mats):
    return (fn_parts, fn_combine, mats, set(mats.keys()))

WHITE, GREY, DARK = hexc('#f6f1ea'), hexc('#8b8f9a'), hexc('#22242c')

def rocket(base=(2.15, -1.3, -0.3), sc=0.9):
    b = V(*base)
    def parts(p):
        q = (p - b) / sc; d = {}
        d['r_body'] = cyl(q, V(0, 1.35, 0), 0.62, 1.15, 0.2)
        d['r_nose'] = tcap(q, V(0, 2.4, 0), V(0, 3.45, 0), 0.62, 0.07)
        fins = [ell(q @ ry(a), V(0.82, 0.55, 0), V(0.46, 0.6, 0.09)) for a in (0.0, 2.094, 4.188)]
        d['r_fin'] = np.min(np.stack(fins, 0), 0)
        d['r_ring'] = torz(q, V(0, 1.75, 0.56), 0.28, 0.075)
        d['r_glass'] = ell(q, V(0, 1.75, 0.6), V(0.26, 0.26, 0.11))
        d['r_band'] = tory(q, V(0, 0.75, 0), 0.63, 0.05)
        d['r_flame'] = tcap(q, V(0, 0.2, 0), V(0, -0.75, 0), 0.36, 0.03)
        cl = [sph(q, V(np.cos(a) * 0.95, 0.0, np.sin(a) * 0.95), 0.46) for a in np.linspace(0, 6.283, 7)[:-1]]
        d['r_cloud'] = np.min(np.stack(cl, 0), 0)
        return {k: v * sc for k, v in d.items()}
    def comb(d):
        o = smin(d['r_body'], d['r_nose'], 0.06 * sc)
        for k in ('r_fin', 'r_ring', 'r_band', 'r_glass', 'r_flame'): o = np.minimum(o, d[k])
        return np.minimum(o, d['r_cloud'])
    def glass(p):
        n = p.shape[0]; return np.broadcast_to(hexc('#8fd0ff'), (n, 3)).copy(), 2.5, 160, 0.5, np.broadcast_to(V(0.05, 0.16, 0.35), (n, 3)).copy()
    def flame(p):
        n = p.shape[0]; return np.broadcast_to(hexc('#ff9a3d'), (n, 3)).copy(), 0, 1, 0, np.broadcast_to(V(1.6, 0.6, 0.12), (n, 3)).copy()
    return prop(parts, comb, dict(r_body=K(WHITE, 0.9, 60, 0.12), r_nose=K(hexc('#5a5c68'), 1.2, 70, 0.3), r_fin=K(hexc('#5a5c68'), 0.8, 60, 0.2),
        r_ring=K(hexc('#2c2c34'), 1.0, 60, 0.2), r_glass=glass, r_band=K(hexc('#6a3df0'), 0.6, 40, 0.1), r_flame=flame, r_cloud=K(WHITE, 0.05, 8, 0.0)))

def computer(base=(2.0, -1.42, -0.1), yaw=-0.42):
    b = V(*base); R = ry(yaw)
    def parts(p):
        q = (p - b) @ R; d = {}
        d['c_desk'] = box(q, V(0, 0.42, 0), V(1.25, 0.42, 0.85), 0.08)
        d['c_mon'] = box(q, V(0, 1.6, -0.1), V(0.95, 0.78, 0.68), 0.14)
        d['c_scr'] = box(q, V(0, 1.6, 0.62), V(0.7, 0.58, 0.05), 0.02)
        d['c_kb'] = box(q, V(0, 0.9, 0.55), V(0.7, 0.05, 0.26), 0.03)
        d['c_drv'] = box(q, V(0.85, 1.0, 0.1), V(0.42, 0.14, 0.42), 0.05)
        return d
    def comb(d): return np.minimum(np.minimum(d['c_desk'], d['c_mon']), np.minimum(d['c_kb'], np.minimum(d['c_scr'], d['c_drv'])))
    def scr(p):
        q = (p - b) @ R; n = p.shape[0]
        u = (q[:, 0] + 0.7) / 1.4; v = (q[:, 1] - 1.02) / 1.16
        bars = sstep(0.4, 0.5, np.abs(np.sin(v * 22)))
        e = mix(np.broadcast_to(V(0.35, 0.08, 0.9), (n, 3)), np.broadcast_to(V(0.25, 0.6, 1.0), (n, 3)), np.clip(u * 0.8 + 0.1, 0, 1)) * (0.5 + 0.5 * bars)[:, None]
        return np.broadcast_to(V(0.05, 0.05, 0.1), (n, 3)).copy(), 2.0, 120, 0.3, e * 0.55
    def kb(p):
        q = (p - b) @ R; n = p.shape[0]
        keys = sstep(0.35, 0.5, np.abs(np.sin(q[:, 0] * 30))) * sstep(0.35, 0.5, np.abs(np.sin(q[:, 2] * 28)))
        return mix(np.broadcast_to(hexc('#1a1b20'), (n, 3)), np.broadcast_to(hexc('#d8d8de'), (n, 3)), keys), 0.4, 40, 0.05, np.zeros((n, 3), F)
    return prop(parts, comb, dict(c_desk=K(hexc('#2c2d36'), 0.4, 40, 0.1), c_mon=K(hexc('#d5d6dc'), 0.7, 50, 0.1), c_scr=scr, c_kb=kb, c_drv=K(hexc('#c9cad1'), 0.5, 40, 0.08)))

def globe(base=(2.2, -1.42, -0.2), sc=0.9):
    b = V(*base)
    def parts(p):
        q = (p - b) / sc; d = {}
        d['g_ped'] = np.minimum(cyl(q, V(0, 0.15, 0), 1.1, 0.15, 0.06), cyl(q, V(0, 0.42, 0), 0.75, 0.12, 0.05))
        d['g_globe'] = sph(q, V(0, 1.75, 0), 1.0)
        d['g_ring'] = tory(q @ rz(0.5) @ rx(0.25), V(0, 0, 0) + (V(0, 1.75, 0) @ (rz(0.5) @ rx(0.25))[:, :]) * 0 + V(0, 0, 0), 1.45, 0.035) if False else torz(q @ rx(1.2), V(0, 0, -1.75 * np.sin(1.2)) if False else (V(0, 1.75, 0) @ rx(1.2)), 1.45, 0.035)
        bl = []
        for c, a in ((V(-1.7, 2.7, 0.3), 0.6), (V(1.6, 3.0, 0.4), -0.5), (V(-1.5, 1.2, 0.8), -0.8), (V(1.7, 1.6, -0.2), 0.7)):
            bl.append(box(q, c, V(0.42, 0.015, 0.22), 0.012, rz(a) @ rx(0.5)))
        d['g_bill'] = np.min(np.stack(bl, 0), 0)
        return {k: v * sc for k, v in d.items()}
    def comb(d): return np.minimum(np.minimum(d['g_ped'], d['g_globe']), np.minimum(d['g_ring'], d['g_bill']))
    def gl(p):
        q = (p - b) / sc; n = p.shape[0]
        land = sstep(0.52, 0.58, vnoise(q * 2.4 + 3.0) * 0.6 + vnoise(q * 5.0) * 0.4)
        return mix(np.broadcast_to(hexc('#3b82f6'), (n, 3)), np.broadcast_to(hexc('#5bbf72'), (n, 3)), land), 1.6, 90, 0.3, np.broadcast_to(V(0.02, 0.05, 0.12), (n, 3)).copy()
    return prop(parts, comb, dict(g_ped=K(hexc('#b9bcc6'), 1.2, 70, 0.35), g_globe=gl, g_ring=K(WHITE, 0.6, 50, 0.1), g_bill=K(hexc('#66c47a'), 0.3, 30, 0.05)))

def shield(base=(2.2, -1.42, -0.2), sc=0.9):
    b = V(*base)
    def parts(p):
        q = (p - b) / sc; d = {}
        qs = q - V(0, 1.9, 0)
        x, y = qs[:, 0], qs[:, 1]
        box2 = np.maximum(np.abs(x) - 0.95, np.abs(y - 0.55) - 0.7)
        ell2 = (L(np.stack([x / 0.95, (y + 0.15) / 1.4], -1)) - 1) * 0.95
        d2 = np.where(y > -0.15, box2, ell2)
        w = np.stack([d2, np.abs(qs[:, 2]) - 0.14], -1)
        d['s_shield'] = np.minimum(w.max(-1), 0) + L(np.maximum(w, 0)) - 0.09
        d['s_base'] = cyl(q, V(0, 0.12, 0), 1.25, 0.12, 0.05)
        d['s_head'] = sph(q, V(0, 2.55, 0.26), 0.19)
        d['s_body'] = ell(q, V(0, 2.1, 0.26), V(0.34, 0.34, 0.09))
        d['s_lock'] = box(q, V(-1.05, 0.9, 0.5), V(0.28, 0.24, 0.13), 0.05)
        d['s_shack'] = torz(q, V(-1.05, 1.22, 0.5), 0.17, 0.05)
        return {k: v * sc for k, v in d.items()}
    def comb(d):
        o = np.minimum(d['s_shield'], d['s_base']); o = np.minimum(o, np.minimum(d['s_head'], d['s_body']))
        return np.minimum(o, np.minimum(d['s_lock'], d['s_shack']))
    gold = K(hexc('#f3c145'), 1.6, 70, 0.4)
    return prop(parts, comb, dict(s_shield=K(hexc('#8d93a8'), 1.6, 80, 0.5), s_base=K(hexc('#4b4c56'), 1.0, 60, 0.3), s_head=K(hexc('#6a3df0'), 0.6, 40, 0.1), s_body=K(hexc('#6a3df0'), 0.6, 40, 0.1), s_lock=gold, s_shack=gold))

def crate(base=(1.35, -1.42, 0.95), yaw=0.4):
    b = V(*base); R = ry(yaw)
    def parts(p):
        q = (p - b) @ R; d = {}
        d['k_box'] = box(q, V(0, 0.5, 0), V(0.56, 0.5, 0.5), 0.05)
        d['k_tape'] = box(q, V(0, 0.5, 0), V(0.09, 0.53, 0.53), 0.02)
        cs = [cyl(q, V(0.02 * i, 1.08 + 0.1 * i, 0.03 * i), 0.24, 0.045, 0.02) for i in range(3)]
        d['k_coin'] = np.min(np.stack(cs, 0), 0)
        return d
    def comb(d): return np.minimum(d['k_box'], np.minimum(d['k_tape'], d['k_coin']))
    return prop(parts, comb, dict(k_box=K(hexc('#c18f54'), 0.15, 20, 0.02), k_tape=K(WHITE, 0.4, 30, 0.05), k_coin=K(hexc('#f5c542'), 2.0, 80, 0.5)))

def book(base=(0.0, -0.55, 1.0), tilt=-0.4):
    b = V(*base); R = rx(tilt)
    def parts(p):
        q = (p - b) @ R; d = {}
        d['b_cover'] = box(q, V(0, 0, 0), V(0.5, 0.62, 0.09), 0.04)
        d['b_pages'] = box(q, V(0.04, 0, 0.0), V(0.48, 0.58, 0.085), 0.02)
        return d
    def pages(p):
        q = (p - b) @ R; n = p.shape[0]; edge = sstep(0.43, 0.47, q[:, 0])
        return mix(np.broadcast_to(hexc('#2a0e8a'), (n, 3)), np.broadcast_to(hexc('#f4ecdc'), (n, 3)), edge), 0.12, 30, 0.03, np.zeros((n, 3), F)
    return prop(parts, lambda d: np.minimum(d['b_cover'], d['b_pages']), dict(b_cover=K(hexc('#2a0e8a'), 0.15, 30, 0.04), b_pages=pages))

def hero_props(v, pkg, lift1, lift2, mv):
    st = V(0, -1.47, 0)
    def parts(p):
        d = {}
        d['h_stage'] = cyl(p, st, 4.4, 0.05, 0.03)
        for nm, sg in (('c', -1), ('f', 1)):
            d['h_ped' + nm] = box(p, V(sg * 3.0, -1.22, 0.3), V(0.62, 0.17, 0.62), 0.06)
            d['h_disc' + nm] = cyl(p, V(sg * 3.0, -1.02, 0.3), 0.36, 0.03, 0.02)
        pts = [V(-3.0, -1.0, 0.3), V(-2.1, -1.2, 1.55), V(2.1, -1.2, 1.55), V(3.0, -1.0, 0.3)]
        rl = [tcap(p, pts[i], pts[i + 1], 0.07, 0.07) for i in range(3)]
        d['h_rail'] = np.min(np.stack(rl, 0), 0)
        d['h_pkg'] = box(p, pkg, V(0.24, 0.17, 0.24), 0.06, ry(mv * 6.283))
        Rm = ry(0.22) @ rx(-0.12)
        d['h_meter'] = box(p, V(-1.0, -1.36, 2.4), V(0.9, 0.03, 0.58), 0.02, Rm)
        return d
    def comb(d):
        o = np.minimum(d['h_stage'], d['h_rail'])
        for k in ('h_pedc', 'h_pedf', 'h_discc', 'h_discf', 'h_pkg', 'h_meter'): o = np.minimum(o, d[k])
        return o
    def meter(p):
        Rm = ry(0.22) @ rx(-0.12); q = (p - V(-1.0, -1.36, 2.4)) @ Rm; n = p.shape[0]
        u = (q[:, 0] + 0.9) / 1.8; w = (q[:, 2] + 0.58) / 1.16
        fr = (u * 24) % 1.0; major = ((np.floor(u * 24)) % 5 == 0)
        tick = (fr < 0.2) & (w > np.where(major, 0.35, 0.5)) & (w < 0.85)
        fill = (w < 0.22) & (u < v)
        needle = (np.abs(u - v) < 0.012) & (w > 0.2) & (w < 0.92)
        c = np.broadcast_to(hexc('#efe7cd'), (n, 3)).copy()
        c[tick] = hexc('#2a2a30'); c[fill] = hexc('#6a3df0'); c[needle] = hexc('#e23b3b')
        return c, 0.3, 30, 0.05, np.where(needle[:, None], V(0.9, 0.1, 0.1), V(0, 0, 0)).astype(F) * (0.6 + v)
    def lit(p):
        n = p.shape[0]; return np.broadcast_to(hexc('#f6df8a'), (n, 3)).copy(), 0.5, 30, 0.1, np.broadcast_to(V(0.9, 0.7, 0.2), (n, 3)).copy() * 0.6
    def pk(p):
        n = p.shape[0]; return np.broadcast_to(hexc('#f7c948'), (n, 3)).copy(), 1.5, 60, 0.25, np.broadcast_to(V(0.5, 0.35, 0.05), (n, 3)).copy()
    return prop(parts, comb, dict(h_stage=K(hexc('#1b2240'), 0.8, 60, 0.25), h_pedc=K(hexc('#3c4a6b'), 0.5, 40, 0.1), h_pedf=K(hexc('#3c4a6b'), 0.5, 40, 0.1),
        h_discc=lit, h_discf=lit, h_rail=K(hexc('#d5d8e0'), 1.6, 80, 0.5), h_pkg=pk, h_meter=meter))

def dome_scene(x, lift):
    c = V(x, -1.05 + lift, 0.3)
    def parts(p): return {'d_dome': np.maximum(L(p - c) - 0.78, -(p[:, 1] - (-1.05 + lift) + 0.03))}
    def mat(name, p):
        n = p.shape[0]; return np.broadcast_to(V(0.1, 0.1, 0.2), (n, 3)).copy(), 2.4, 120, 0.7, np.zeros((n, 3), F)
    return Scene(parts, lambda d: d['d_dome'], mat, ((x, -0.8, 0.3), 1.05), None)
