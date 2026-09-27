import subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from bidi.algorithm import get_display
S = "/tmp/claude-0/-home-user-studio-manager/9d672da4-0fff-50da-bbb9-5e44a324e464/scratchpad"
FONT = f"{S}/fonts/fontsource-frank-ruhl-libre-5.2.8/files/frank-ruhl-libre-hebrew-400-normal.woff"
import glob
FONT = f"{S}/fonts/frank-ruhl-libre-merged.ttf"
SMALL = f"{S}/fonts/heebo-merged.ttf"
W, H = 720, 1280

def text_png(path, lines, y=0.2):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(img), ImageDraw.Draw(shadow)
    cy = int(H * y)
    for txt, size, font in lines:
        f = ImageFont.truetype(font, size)
        t = txt
        bw = d.textlength(t, font=f, direction='rtl')
        x = (W - bw) / 2
        sd.text((x, cy), t, font=f, fill=(0, 0, 0, 150), direction='rtl')
        d.text((x, cy), t, font=f, fill=(255, 255, 255, 255), direction='rtl')
        cy += int(size * 1.35)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    Image.alpha_composite(shadow, img).save(path)

def T(big, small=None):
    l = [(big, 62, FONT)]
    if small: l.append((small, 34, SMALL))
    return l

C = lambda i: f"{S}/clip{i}.mp4"
LOGO = (2, 10.35, 12.4)

REELS = {
 "reel1_drape": dict(
   segs=[(4,0.1,0.6),(4,4.8,5.7),(4,6.8,7.85),(4,3.76,4.75),(4,7.9,8.88),(4,10.02,10.95),
         (4,12.5,13.6),(4,14.63,15.58),(5,8.86,10.3),(5,14.83,16.28),(4,15.63,16.95),LOGO],
   texts=[(0.2,2.4,T("חולצה אחת.")),(2.7,5.4,T("כל צבע — לוק אחר.")),
          (5.9,8.9,T("עם סאטן לשבת,","או פשוט ליום־יום")),(9.3,11.55,T("איזה צבע הבא","בארון שלך?"))]),
 "reel2_satin_shabbat": dict(
   segs=[(3,1.96,3.05),(2,0.05,2.4),(3,6.36,7.48),(2,2.46,3.7),(3,7.53,8.64),(2,5.26,6.8),
         (5,0.05,1.5),(3,3.1,4.9),(5,17.83,19.0),(2,6.8,8.74),LOGO],
   texts=[(0.2,2.8,T("סט סאטן לשבת.")),(3.2,6.6,T("לא רק לחג —","לכל שבוע")),
          (7.4,10.6,T("נופל רך. מבריק בעדינות.")),(11.4,14.6,T("שבת שלום,","בסטייל שקט"))]),
 "reel3_duo_colors": dict(
   segs=[(3,0.05,1.9),(3,3.1,4.9),(5,0.05,1.5),(3,8.7,10.57),(5,3.13,4.4),(5,10.36,11.8),
         (3,10.63,11.64),(5,16.33,17.77),(3,11.7,12.97),LOGO],
   texts=[(0.2,2.6,T("חום או שמנת?")),(3.2,6.6,T("אותו סט סאטן,","שתי אנרגיות")),
          (7.4,10.6,T("שלה בחום. שלך בשמנת?")),(11.2,13.7,T("או שפשוט — שניהם."))]),
}

for name, r in REELS.items():
    args = ["ffmpeg", "-v", "error", "-y"]
    srcs = sorted({s[0] for s in r["segs"]})
    idx = {c: i for i, c in enumerate(srcs)}
    for c in srcs: args += ["-i", C(c)]
    fc, labels, t = [], [], 0
    for k, (c, a, b) in enumerate(r["segs"]):
        fc.append(f"[{idx[c]}:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30,scale={W}:{H},setsar=1[s{k}]")
        labels.append(f"[s{k}]"); t += b - a
    fc.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[v0]")
    cur = "v0"; n = len(srcs)
    for j, (st, en, lines) in enumerate(r["texts"]):
        p = f"{S}/build/{name}_t{j}.png"; text_png(p, lines)
        args += ["-loop", "1", "-framerate", "30", "-i", p]
        d = en - st
        fc.append(f"[{n}:v]format=rgba,trim=duration={d},fade=in:st=0:d=0.35:alpha=1,fade=out:st={d-0.35}:d=0.35:alpha=1,setpts=PTS-STARTPTS+{st}/TB[t{j}]")
        fc.append(f"[{cur}][t{j}]overlay=0:0:eof_action=pass[o{j}]"); cur = f"o{j}"; n += 1
    args += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    args += ["-filter_complex", ";".join(fc), "-map", f"[{cur}]", "-map", f"{n}:a",
             "-t", f"{t:.2f}", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", f"{S}/build/{name}.mp4"]
    subprocess.run(args, check=True)
    print(name, round(t, 2), "s")
