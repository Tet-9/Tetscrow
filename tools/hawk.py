from sdf import *

C = dict(brown=hexc('#4b3222'), brown2=hexc('#704b33'), cream=hexc('#f4e6ca'), beak=hexc('#f6b93a'), dark=hexc('#2a1b12'),
         eyeW=hexc('#fff6cf'), iris=hexc('#f28c1c'), pupil=hexc('#060606'), pink=hexc('#dd5c6c'), tip=hexc('#3a2a16'), glass=hexc('#b9dcff'))

def make_hawk(pos=(0, 0, 0), yaw=0.0, wave=0.0, waveL=0.0, blink=0.0, flash=0.0, glasses=False, scale=1.0, headyaw=0.0, armF=0.0):
    pos = V(*pos); R = ry(yaw); Rh = ry(headyaw)
    def lp(p): return ((p - pos) @ R) / scale
    sh_r = V(0.86, 0.72, 0.0); sh_l = V(-0.86, 0.72, 0.0)
    def parts(p):
        q = lp(p); s = scale; d = {}
        d['body'] = ell(q, V(0, 0, 0), V(1.0, 1.12, 0.92))
        d['belly'] = ell(q, V(0, -0.14, 0.3), V(0.74, 0.9, 0.66))
        qh = (q - V(0, 1.1, 0.1)) @ Rh + V(0, 1.1, 0.1)
        d['head'] = ell(qh, V(0, 1.1, 0.1), V(0.76, 0.72, 0.76))
        br = []
        for sg in (-1, 1):
            c = V(sg * 0.37, 1.31, 0.6); r_ = qh - c; r_ = r_ + V(0, -0.55 * sg * r_[:, 0], 0).T if False else r_
            r2 = np.stack([r_[:, 0], r_[:, 1] - 0.75 * sg * r_[:, 0], r_[:, 2]], -1)
            br.append(ell(r2 + c, c, V(0.36, 0.11, 0.27)))
        d['brow'] = np.minimum(br[0], br[1])
        ey = []
        for sg in (-1, 1):
            ey.append(ell(qh, V(sg * 0.4, 1.08, 0.58), V(0.19, 0.19 * (1 - 0.92 * blink) + 0.01, 0.19)))
        d['eye'] = np.minimum(ey[0], ey[1])
        d['beak'] = np.minimum(tcap(qh, V(0, 0.98, 0.6), V(0, 0.84, 1.22), 0.25, 0.06), tcap(qh, V(0, 0.84, 1.22), V(0, 0.58, 1.16), 0.065, 0.03))
        d['beakL'] = tcap(qh, V(0, 0.8, 0.6), V(0, 0.68, 1.04), 0.15, 0.05)
        d['tongue'] = sph(qh, V(0, 0.77, 0.86), 0.08)
        d['tufts'] = ell(qh, V(0, 1.62, -0.28), V(0.3, 0.12, 0.26), rx(-0.5))
        for sg, sh, ang, fw in ((1, sh_r, wave, armF), (-1, sh_l, waveL, 0.0)):
            th = sg * (0.1 + ang)
            Rw = rz(th) @ rx(-fw)
            wq = (q - sh) @ Rw
            w1 = ell(wq, V(sg * 0.08, -0.5, -0.05), V(0.3, 0.82, 0.5))
            tips = np.minimum(np.minimum(ell(wq, V(sg * 0.06, -1.25, -0.22), V(0.11, 0.3, 0.1)), ell(wq, V(sg * 0.06, -1.32, 0.0), V(0.11, 0.3, 0.1))), ell(wq, V(sg * 0.06, -1.25, 0.22), V(0.11, 0.3, 0.1)))
            d['wing' + str(sg)] = w1; d['tips' + str(sg)] = tips
        d['tail'] = ell(q, V(0, -0.85, -1.0), V(0.55, 0.14, 0.62), rx(0.35))
        legs, toes = [], []
        for sg in (-1, 1):
            legs.append(tcap(q, V(sg * 0.4, -0.95, 0.2), V(sg * 0.4, -1.32, 0.3), 0.12, 0.09))
            for k in (-1, 0, 1):
                toes.append(tcap(q, V(sg * 0.4, -1.32, 0.3), V(sg * 0.4 + k * 0.2, -1.36, 0.78), 0.085, 0.05))
        d['legs'] = np.minimum(legs[0], legs[1]); d['toes'] = np.min(np.stack(toes, 0), 0)
        if glasses:
            g = []
            for sg in (-1, 1): g.append(torz(qh, V(sg * 0.37, 1.13, 0.74), 0.3, 0.035))
            g.append(tcap(qh, V(-0.07, 1.16, 0.76), V(0.07, 1.16, 0.76), 0.03, 0.03))
            d['glasses'] = np.min(np.stack(g, 0), 0)
        return {k: v * scale for k, v in d.items()}
    def combine(d):
        o = smin(smin(d['body'], d['head'], 0.38 * scale), d['belly'], 0.14 * scale)
        o = smin(o, d['tail'], 0.2 * scale)
        for k in ('wing1', 'wing-1'): o = smin(o, d[k], 0.1 * scale)
        for k in ('tips1', 'tips-1'): o = smin(o, d[k], 0.05 * scale)
        o = smin(o, d['brow'], 0.07 * scale); o = smin(o, d['tufts'], 0.1 * scale); o = smin(o, d['beak'], 0.05 * scale)
        o = np.minimum(o, np.minimum(d['eye'], d['beakL'])); o = np.minimum(o, d['tongue'])
        o = np.minimum(o, np.minimum(d['legs'], d['toes']))
        if 'glasses' in d: o = np.minimum(o, d['glasses'])
        return o
    def mat(name, p):
        q = lp(p); n = q.shape[0]; ones = np.ones(n, F)
        qh = (q - V(0, 1.1, 0.1)) @ Rh + V(0, 1.1, 0.1)
        z = np.zeros((n, 3), F)
        def col(c): return np.broadcast_to(c, (n, 3)).copy()
        if name == 'body':
            v = vnoise(q * 6)[:, None]
            return mix(col(C['brown']), col(C['brown2']), np.clip(v[:, 0] * 0.8, 0, 1)), 0.12, 16, 0.03, z
        if name == 'belly':
            dots = sstep(0.66, 0.74, vnoise(q * V(30, 7, 30)))
            band = np.exp(-(((q[:, 1] + 0.0) / 0.2) ** 2)) * sstep(0.1, 0.5, q[:, 2])
            m = np.clip(dots * 0.9 * sstep(-0.9, 0.0, q[:, 1] + 0.6) + band * 0.5, 0, 1)
            return mix(col(C['cream']), col(C['brown2']), m), 0.1, 16, 0.03, z
        if name == 'head':
            throat = sstep(0.12, -0.02, np.abs(qh[:, 0]) - 0.26) * sstep(0.95, 0.75, qh[:, 1]) * sstep(0.2, 0.5, qh[:, 2])
            cheek = sstep(0.75, 0.55, qh[:, 1]) * 0.6
            base = mix(col(C['brown']), col(C['brown2']), np.clip(vnoise(qh * 9) * 0.7, 0, 1))
            base = mix(base, col(C['cream']), np.clip(throat + cheek * sstep(0.1, 0.4, qh[:, 2]), 0, 1))
            eyec = np.stack([np.sign(qh[:, 0] + 1e-6) * 0.4, 1.08 * ones, 0.58 * ones], -1)
            stripe = sstep(0.42, 0.2, L(qh - eyec)) * 0.85
            return mix(base, col(C['dark']), stripe), 0.12, 16, 0.03, z
        if name in ('brow', 'tufts'): return col(C['dark']), 0.1, 14, 0.02, z
        if name == 'eye':
            sg = np.sign(qh[:, 0] + 1e-6); c = np.stack([sg * 0.37, 1.13 * ones, 0.62 * ones], -1)
            v = nrm(qh - c); f = nrm(np.stack([sg * 0.18, 0 * ones, 1 * ones], -1)); ca = (v * f).sum(-1)
            iris = sstep(0.62, 0.66, ca); pup = sstep(0.9, 0.915, ca)
            cc = mix(col(C['eyeW']), col(C['iris']), iris); cc = mix(cc, col(C['pupil']), pup)
            return cc, 2.6, 180, 0.4, np.stack([0.15 * ones, 1.0 * ones, 0.35 * ones], -1) * (flash * iris * (1 - pup) * 1.6)[:, None]
        if name in ('beak', 'beakL'):
            tipm = sstep(0.98, 1.08, qh[:, 2]) * (qh[:, 1] < 0.9 if name == 'beak' else 0) + 0
            return mix(col(C['beak']), col(C['tip']), np.clip(sstep(1.15, 1.22, qh[:, 2]) * 0.95, 0, 1)), 1.0, 60, 0.15, z
        if name == 'tongue': return col(C['pink']), 0.6, 30, 0.05, z
        if name.startswith('wing'):
            bands = 0.5 + 0.5 * np.sin(q[:, 1] * 15 + vnoise(q * 8) * 3)
            return mix(col(C['brown']), col(C['brown2']), bands * 0.7), 0.12, 18, 0.03, z
        if name.startswith('tips'): return col(C['cream']), 0.12, 18, 0.03, z
        if name == 'tail':
            return mix(col(C['brown2']), col(C['cream']), sstep(-1.35, -1.55, q[:, 2]) * ones), 0.1, 16, 0.02, z
        if name in ('legs', 'toes'): return col(C['beak']), 0.4, 32, 0.06, z
        if name == 'glasses': return col(C['glass']), 1.2, 90, 0.4, z
        return col(C['brown']), 0.1, 16, 0.02, z
    return parts, combine, mat
