import sys, time, os, math
sys.path.insert(0, '/home/claude/tet/tools')
from sdf import *; from hawk import make_hawk; from scenes import *
from PIL import ImageDraw, ImageFont
OUT = '/home/claude/tet/frontend/assets/hero'; os.makedirs(OUT, exist_ok=True)
N, W, H = 24, 512, 384
CAM = (0.0, 3.6, 15.6); TGT = (0.0, -0.3, 0.4); FOV = 29
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
PTS = [V(-3.0, -0.8, 0.3), V(-2.1, -0.98, 1.55), V(2.1, -0.98, 1.55), V(3.0, -0.8, 0.3)]
def along(t):
    seg = [float(L((PTS[i + 1] - PTS[i])[None, :])[0]) for i in range(3)]; tot = sum(seg); d = t * tot
    for i in range(3):
        if d <= seg[i] or i == 2:
            u = min(d / seg[i], 1.0); return PTS[i] + (PTS[i + 1] - PTS[i]) * u
        d -= seg[i]
def project(pt):
    cp, tg = V(*CAM), V(*TGT); fw = nrm((tg - cp)[None, :])[0]; rt = nrm(np.cross(fw, V(0, 1, 0))[None, :])[0]; up = np.cross(rt, fw)
    v = V(*pt) - cp; z = float(v @ fw); k = math.tan(math.radians(FOV) / 2)
    return (float(v @ rt) / (z * k * (W / H)) * 0.5 + 0.5) * W, (0.5 - float(v @ up) / (z * k) * 0.5) * H
def frame(i):
    p = i / (N - 1); tt = ease((p - 0.2) / 0.55)
    pk = along(tt) + V(0, 0.1 * math.sin(math.pi * tt), 0)
    l1 = ease(p / 0.15) - ease((p - 0.28) / 0.12); l2 = ease((p - 0.68) / 0.12) - ease((p - 0.92) / 0.08)
    flash = ease((tt - 0.35) / 0.07) * (1 - ease((tt - 0.62) / 0.08))
    blink = math.exp(-((p - 0.5) / 0.018) ** 2) + math.exp(-((p - 0.66) / 0.018) ** 2)
    hy = 0.55 * math.atan2(float(pk[0]), 3.4)
    hawk = make_hawk(pos=(0, 0, 0), yaw=0.0, blink=min(blink, 1), flash=flash, headyaw=hy)
    sc = compose(hawk, [hero_props(tt, pk, l1, l2, tt)], ((0, -0.2, 0.6), 6.4), ground=-1.42)
    img = render(sc, W, H, cam_pos=CAM, target=TGT, fov=FOV, ss=2)
    for x, lift in ((-3.0, 1.3 * l1), (3.0, 1.3 * l2)):
        ds = dome_scene(x, lift)
        d = render(ds, W, H, cam_pos=CAM, target=TGT, fov=FOV, ss=2, shadow_ground=False)
        a = np.asarray(d).astype(np.float32); lum = a[..., :3].mean(-1) / 255.0
        al = np.clip((lum - 0.06) * 1.3, 0, 0.6) * (a[..., 3] / 255.0)
        layer = np.dstack([a[..., :3], al * 255]).astype(np.uint8)
        img.alpha_composite(Image.fromarray(layer, 'RGBA'))
    dr = ImageDraw.Draw(img)
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 11)
    except Exception: font = ImageFont.load_default()
    for txt, x in (('CLIENT', -3.35), ('FREELANCER', 3.35)):
        cx, cy = project((x, -1.36, 1.0)); tw = dr.textlength(txt, font=font)
        dr.rounded_rectangle((cx - tw / 2 - 8, cy - 9, cx + tw / 2 + 8, cy + 9), 9, fill=(28, 34, 56, 235))
        dr.text((cx - tw / 2, cy - 7), txt, fill=(255, 255, 255, 255), font=font)
    img.save(f'{OUT}/f{i:03d}.webp', 'WEBP', quality=84, method=4)
if __name__ == '__main__':
    a = sys.argv[1:]; rng = range(N) if not a else [int(x) for x in a]
    for i in rng:
        t = time.time(); frame(i); print(i, round(time.time() - t), 's', flush=True)
