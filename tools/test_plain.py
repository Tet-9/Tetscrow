import time, sys
sys.path.insert(0, '/home/claude/tet/tools')
from sdf import *; from hawk import make_hawk
hp, hc, hm = make_hawk(yaw=0.42, wave=0.0)
sc = Scene(hp, hc, hm, bound=((0, 0.2, 0), 2.7), ground=-1.42)
t = time.time()
img = render(sc, 360, 360, cam_pos=(0.5, 1.4, 11.5), target=(0, 0.15, 0), fov=26, ss=2)
print('render s:', round(time.time() - t, 1))
bg = Image.new('RGBA', img.size, (183, 156, 255, 255)); bg.alpha_composite(img); bg.convert('RGB').save('/tmp/hawk_test.png')
