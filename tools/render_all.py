import sys, time, os
sys.path.insert(0, '/home/claude/tet/tools')
from sdf import *; from hawk import make_hawk; from scenes import *
OUT = '/home/claude/tet/frontend/assets'; os.makedirs(OUT, exist_ok=True)
CAM = dict(fov=31, ss=2)

def still(name):
    if name == 'rocket':
        sc = compose(make_hawk(pos=(-1.3, 0, 0.1), yaw=0.55, wave=1.25), [rocket()], ((0.6, 0.9, 0), 4.6)); size = (480, 480); cam = ((0.4, 1.6, 13.5), (0.35, 0.6, 0))
    elif name == 'computer':
        sc = compose(make_hawk(pos=(-1.7, 0, 0.3), yaw=1.05, armF=0.9), [computer()], ((0.2, 0.7, 0), 4.6)); size = (560, 420); cam = ((0.3, 1.8, 13.8), (0.2, 0.55, 0))
    elif name == 'globe':
        sc = compose(make_hawk(pos=(-1.4, 0, 0.2), yaw=0.5, wave=1.2), [globe()], ((0.7, 0.9, 0), 4.7)); size = (480, 480); cam = ((0.4, 1.6, 13.8), (0.4, 0.75, 0))
    elif name == 'shield':
        sc = compose(make_hawk(pos=(-1.4, 0, 0.2), yaw=0.55), [shield()], ((0.7, 1.0, 0), 4.8)); size = (480, 480); cam = ((0.4, 1.6, 13.8), (0.4, 0.8, 0))
    elif name == 'receiver':
        sc = compose(make_hawk(pos=(-0.3, 0, 0), yaw=-0.3, armF=0.5), [crate()], ((0.4, 0.4, 0.5), 3.6)); size = (420, 420); cam = ((0.3, 1.5, 11), (0.35, 0.15, 0.2))
    elif name == 'sender':
        sc = compose(make_hawk(pos=(0, 0, 0), yaw=-0.2, glasses=True, armF=0.8), [book()], ((0, 0.4, 0.5), 3.4), ground=-1.42); size = (420, 420); cam = ((0.2, 1.4, 11), (0.0, 0.2, 0.2))
    elif name == 'plain':
        sc = compose(make_hawk(pos=(0, 0, 0), yaw=0.35, wave=1.25), [], ((0, 0.3, 0), 2.9)); size = (420, 420); cam = ((0.6, 1.5, 11), (0, 0.2, 0))
    t = time.time()
    img = render(sc, size[0], size[1], cam_pos=cam[0], target=cam[1], **CAM)
    img.save(f'{OUT}/hawk-{name}.png', optimize=True)
    print(name, round(time.time() - t), 's', flush=True)

if __name__ == '__main__':
    for n in sys.argv[1:]: still(n)
