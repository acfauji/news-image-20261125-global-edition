"""Original, parameterized build-time newsroom renderer.

Pillow is used only while building. main.py needs the standard library alone.
Manifest stories are independently sourced; no network access occurs here.
"""
from pathlib import Path
import argparse
import json
import math
from PIL import Image, ImageDraw, ImageFont

PAPER = "#f5f0e4"
INK = "#152d37"
RED = "#a33129"
TEAL = "#247e85"
GOLD = "#d3a757"
MUTED = "#546465"
RULE = "#c4bca9"
WHITE = "#fffcf3"
FONT_DIR = Path("/usr/share/fonts/truetype")
FONTS = {
    "serif": FONT_DIR / "freefont/FreeSerifBold.ttf",
    "sans": FONT_DIR / "lato/Lato-Regular.ttf",
    "bold": FONT_DIR / "lato/Lato-Heavy.ttf",
    "italic": FONT_DIR / "freefont/FreeSerifItalic.ttf",
}
REGIONS = ["Middle East", "Europe", "Africa", "Asia", "Oceania", "North America", "Latin America"]


class Canvas:
    def __init__(self, scale=2, background=PAPER, size=(1024,1024)):
        self.scale = scale
        self.image = Image.new("RGB", (round(size[0] * scale), round(size[1] * scale)), background)
        self.draw = ImageDraw.Draw(self.image)
        self.cache = {}
        self.boxes = []

    def coords(self, values):
        return tuple(round(v * self.scale) for v in values)

    def font(self, size, kind="sans"):
        key = (size, kind)
        if key not in self.cache:
            self.cache[key] = ImageFont.truetype(str(FONTS[kind]), round(size * self.scale))
        return self.cache[key]

    def rect(self, box, fill, outline=None, width=1):
        self.draw.rectangle(self.coords(box), fill=fill, outline=outline, width=max(1, round(width * self.scale)))

    def line(self, points, fill=RULE, width: float=1):
        self.draw.line([self.coords(p) for p in points], fill=fill, width=max(1, round(width * self.scale)), joint="curve")

    def poly(self, points, fill, outline=None):
        self.draw.polygon([self.coords(p) for p in points], fill=fill, outline=outline)

    def ellipse(self, box, fill=None, outline=None, width=1):
        self.draw.ellipse(self.coords(box), fill=fill, outline=outline, width=max(1, round(width * self.scale)))

    def width(self, text, size, kind="sans"):
        return self.draw.textlength(text, font=self.font(size, kind)) / self.scale

    def text(self, xy, text, size=18, fill=INK, kind="sans", anchor=None):
        self.draw.text(self.coords(xy), text, font=self.font(size, kind), fill=fill, anchor=anchor)

    def block(self, xy, text, max_width, size, kind="sans", fill=INK, leading=1.12, max_lines=None):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            trial = (current + " " + word).strip()
            if self.width(trial, size, kind) <= max_width:
                current = trial
            else:
                if not current:
                    raise ValueError("Unbreakable token exceeds text width: " + word)
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        if max_lines and len(lines) > max_lines:
            raise ValueError(f"Text needs {len(lines)} lines, cap {max_lines}: {text}")
        x, y = xy
        for i, line in enumerate(lines):
            self.text((x, y + size * leading * i), line, size, fill, kind)
        h = len(lines) * size * leading
        self.boxes.append({"text": text, "box": [x, y, x + max_width, y + h], "font": size})
        return h

    def save(self, path, colors=224):
        final = self.image.resize((1024, 1024), Image.Resampling.LANCZOS)
        if colors:
            final = final.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        final.save(path, format="PNG", optimize=True)
        final.convert("RGB").resize((300, 300), Image.Resampling.LANCZOS).save(path.with_name(path.stem + "-300.png"), optimize=True)
        path.with_suffix(".layout.json").write_text(json.dumps(self.boxes, indent=2))


def globe(c, x, y, r, dark=False):
    sea = INK if dark else TEAL
    land = GOLD if dark else "#e4d2a6"
    c.ellipse((x-r, y-r, x+r, y+r), sea)
    continents = [
        [(-.82,-.37),(-.5,-.67),(-.14,-.54),(-.22,-.28),(-.46,-.13),(-.47,.08),(-.64,-.01)],
        [(-.37,.1),(-.06,.24),(-.18,.6),(-.35,.83),(-.45,.47)],
        [(-.02,-.42),(.28,-.64),(.67,-.5),(.91,-.16),(.54,-.04),(.31,-.2),(.15,-.11)],
        [(.05,-.05),(.4,.05),(.45,.37),(.2,.66),(.05,.36)],
        [(.59,.47),(.85,.4),(.91,.65),(.64,.68)],
    ]
    for pts in continents:
        c.poly([(x+a*r, y+b*r) for a,b in pts], land)
    c.ellipse((x-r*.72,y-r,x+r*.72,y+r),outline="#ffffff",width=.6)
    c.line([(x-r*.96,y),(x+r*.96,y)],"#ffffff",.6)
    c.ellipse((x-r,y-r,x+r,y+r),outline=INK,width=2)


def illustration(c, box, motif, accent=TEAL):
    """Render to a bounded layer so no artwork bleeds into adjacent captions."""
    x,y,w,h=box
    layer=Canvas(c.scale, size=(w,h))
    illustration_shapes(layer,(0,0,w,h),motif,accent)
    c.image.paste(layer.image,(round(x*c.scale),round(y*c.scale)))


def illustration_shapes(c, box, motif, accent=TEAL):
    """Draw original editorial geometry, not copied images or character art."""
    x,y,w,h = box
    def p(a,b): return (x+a*w,y+b*h)
    def poly(pts,color): c.poly([p(a,b) for a,b in pts],color)
    def line(pts,color=INK,width: float=2): c.line([p(a,b) for a,b in pts],color,width)
    def rect(a,b,d,e,color): c.rect((*p(a,b),*p(d,e)),color)
    def ell(a,b,d,e,color,outline=None): c.ellipse((*p(a,b),*p(d,e)),color,outline)
    rect(0,0,1,1,"#e4e8dc")
    ell(.49,-.2,1.15,.88,"#c8d7c6")
    line([(.02,.79),(.98,.79)],accent,1)
    if motif == "orbital":
        rect(0,0,1,1,INK)
        # Original cutaway orbital scene: Earth, Tiangong arrays and docked capsule.
        ell(-.15,.56,1.2,2.05,TEAL)
        ell(-.15,.58,1.2,2.1,"#6aa5a0")
        poly([(.02,.91),(.18,.71),(.39,.71),(.5,.82),(.37,.95)],"#b7c6a8")
        poly([(.61,.74),(.81,.72),(.97,.92),(.88,1),(.7,.93)],"#b7c6a8")
        for a,b in [(.08,.19),(.27,.23),(.85,.12),(.92,.43),(.66,.08),(.1,.5),(.78,.32)]:
            ell(a,b,a+.004,b+.009,PAPER)
        # Four slatted photovoltaic wings, independently positioned modules.
        for a,b,d,e in [(.15,.25,.35,.4),(.15,.52,.35,.67),(.62,.16,.84,.31),(.62,.43,.84,.58)]:
            rect(a,b,d,e,"#245b71")
            for k in range(1,7):
                xx=a+(d-a)*k/7
                line([(xx,b),(xx,e)],"#6ca7b4",.65)
            for k in range(1,3):
                yy=b+(e-b)*k/3
                line([(a,yy),(d,yy)],"#6ca7b4",.65)
            c.rect((*p(a,b),*p(d,e)),None,GOLD,1)
        line([(.24,.46),(.74,.37)],PAPER,5)
        poly([(.35,.42),(.62,.37),(.65,.44),(.38,.5)],PAPER)
        poly([(.42,.34),(.49,.33),(.56,.57),(.49,.59)],"#d5d4c7")
        rect(.4,.41,.46,.47,RED)
        rect(.53,.39,.58,.44,TEAL)
        for a,b in [(.49,.38),(.5,.43),(.51,.48)]:ell(a,b,a+.017,b+.027,INK)
        # The capsule joins the station; a schematic, not a claimed photograph.
        poly([(.64,.39),(.75,.37),(.81,.42),(.77,.49),(.66,.46)],GOLD)
        poly([(.77,.4),(.85,.4),(.88,.44),(.84,.49),(.77,.47)],PAPER)
        ell(.81,.425,.835,.46,TEAL)
        c.text(p(.05,.06),"SHENZHOU-24 / TIANGONG",max(8,w*.025),PAPER,"bold")
        c.text(p(.05,.89),"CHINA + PAKISTAN",max(8,w*.026),PAPER,"bold")
    elif motif == "garments":
        rect(0,0,1,1,"#e8ddc7")
        for i in range(6):
            a=.06+i*.15
            poly([(a,.8),(a,.36),(a+.13,.26),(a+.13,.8)],"#c5b99e")
        poly([(.2,.3),(.39,.2),(.47,.27),(.54,.27),(.62,.2),(.82,.3),(.74,.48),(.66,.44),(.66,.87),(.36,.87),(.36,.44),(.27,.48)],accent)
        line([(.4,.24),(.47,.33),(.56,.33),(.62,.24)],PAPER,2)
        line([(.39,.79),(.63,.79)],PAPER,1)
        ell(.7,.6,.92,.91,GOLD)
        c.text(p(.81,.76),"36%",max(8,w*.11),INK,"bold",anchor="mm")
    elif motif == "talks":
        # Two delegations and an empty central chair: discussion, not an agreement.
        for a in (.2,.8):
            ell(a-.055,.23,a+.055,.39,GOLD)
            poly([(a-.09,.43),(a+.09,.43),(a+.15,.76),(a-.14,.76)],INK)
            line([(a,.49),(.5,.66)],PAPER,6)
        poly([(.15,.62),(.75,.53),(.98,.77),(.31,.91)],accent)
        poly([(.36,.64),(.52,.62),(.59,.68),(.42,.71)],WHITE)
        line([(.45,.65),(.52,.64)],RED,1)
        ell(.35,.60,.39,.66,GOLD)
        ell(.61,.60,.65,.66,GOLD)
        rect(.48,.31,.54,.53,PAPER)
        rect(.50,.35,.52,.48,accent)
        for a in (.08,.91):
            line([(a,.18),(a,.60)],INK,1)
            poly([(a,.18),(a+.08,.22),(a,.28)],RED)
    elif motif == "economy":
        # Container port, customs gate, diverging trade lanes.
        for i in range(6):
            a=.08+i*.135
            rect(a,.47+(i%2)*.10,a+.12,.72,accent if i%2 else GOLD)
            for k in range(3): line([(a+.02+k*.03,.5+(i%2)*.1),(a+.02+k*.03,.69)],PAPER,.6)
        line([(.18,.42),(.18,.16),(.79,.16),(.87,.37)],INK,4)
        line([(.63,.17),(.63,.42)],INK,2)
        poly([(.04,.75),(.94,.75),(.82,.9),(.2,.9)],INK)
        for j in range(4): line([(.05,.94+j*.015),(.95,.94+j*.015)],accent,.8)
    elif motif == "weather":
        for i in range(4):
            a=.12+i*.21
            rect(a,.36+(i%2)*.08,a+.15,.8,PAPER)
            poly([(a-.02,.37+(i%2)*.08),(a+.075,.24+(i%2)*.08),(a+.17,.37+(i%2)*.08)],INK)
            rect(a+.04,.48,a+.08,.58,GOLD)
        for j in range(7):
            yy=.69+j*.035
            line([(.03,yy),(.25,yy+.02),(.5,yy-.01),(.73,yy+.02),(.98,yy)],accent,4)
        for i in range(10):
            a=.08+i*.09
            line([(a,.04),(a-.04,.19)],INK,1)
        poly([(.53,.8),(.85,.8),(.78,.88),(.58,.88)],GOLD)
    elif motif == "science":
        ell(.15,.05,.9,.85,INK)
        for a,b in [(.23,.19),(.7,.22),(.51,.12),(.8,.47),(.27,.6)]: ell(a,b,a+.012,b+.012,PAPER)
        poly([(.34,.69),(.55,.26),(.67,.62)],PAPER)
        poly([(.55,.26),(.63,.4),(.49,.43)],RED)
        poly([(.37,.65),(.27,.83),(.5,.7)],GOLD)
        ell(.51,.44,.6,.54,accent)
        line([(.14,.88),(.87,.88)],GOLD,3)
    elif motif == "sports":
        for i in range(5):
            c.ellipse((*p(.07+i*.035,.15+i*.05),*p(.93-i*.035,.95-i*.05)),outline=accent,width=2)
        line([(.53,.26),(.47,.48),(.67,.56)],INK,8)
        line([(.48,.47),(.31,.62),(.2,.57)],INK,7)
        line([(.48,.48),(.55,.71),(.78,.75)],INK,7)
        ell(.49,.15,.59,.29,GOLD)
        ell(.79,.7,.88,.86,RED)
    elif motif == "society":
        for i in range(5):
            a=.13+i*.17
            ell(a,.27-(i%2)*.1,a+.1,.43-(i%2)*.1,GOLD)
            rect(a-.015,.46-(i%2)*.1,a+.12,.88,accent if i%2 else INK)
        rect(.29,.55,.72,.78,PAPER)
        line([(.35,.64),(.66,.64)],RED,3)
    else:
        globe(c,x+w*.52,y+h*.49,min(w,h)*.39)
        for i in range(5):
            a=.1+i*.17
            line([(a,.88),(a+.1,.88)],accent,3)
    # Deliberate fine-line frame and baseline keep the art editorial, not a stock icon.
    c.rect((x,y,x+w,y+h),None,INK,1)


def label(c, x,y,text, size=12,fill=RED):
    c.text((x,y),text.upper(),size,fill,"bold")


def masthead(c, name, edition, dark=False):
    if dark:
        c.rect((0,0,1024,138),INK)
    fg = PAPER if dark else INK
    label(c,24,16,"WORLD NEWS / WEDNESDAY",12,GOLD if dark else RED)
    c.text((24,29),name,50,fg,"serif")
    c.text((1000,17),"25 NOVEMBER 2026",26,fg,"bold",anchor="rt")
    c.line([(24,91),(1000,91)],GOLD if dark else INK,2)
    c.text((24,101),edition,13,fg,"sans")


def card(c, s, x,y,w,h, size=19, illustrated=False):
    label(c,x,y,s["region"]+" / "+s["field"],10)
    tx=x
    tw=w
    if illustrated:
        illustration(c,(x+w-108,y,108,h-8),s.get("motif","world"))
        tw-=122
    used=c.block((tx,y+17),s["headline"],tw,size,"bold",max_lines=3)
    if s.get("caption") and y+22+used+27<y+h:
        c.block((tx,y+22+used),s["caption"],tw,12,"sans",max_lines=2)
    c.line([(x,y+h),(x+w,y+h)],RULE,1)


def footer(c, count, regions, edition="PROVISIONAL EDITION"):
    c.line([(24,992),(1000,992)],INK,1)
    c.text((24,1000),f"{count} DISTINCT REPORTS  /  {regions} REGIONS  /  {edition}",10,MUTED,"bold")
    c.text((1000,1000),"25.11.2026",10,INK,"bold",anchor="rt")


def select_stories(stories, count):
    """Preserve the three editorial leads, then protect region and field breadth."""
    chosen=list(stories[:3])
    rest=list(stories[3:])
    regions={s["region"] for s in chosen}
    fields={s["field"] for s in chosen}
    while rest and len(chosen)<count:
        gains=[3*(s["region"] not in regions)+2*(s["field"] not in fields) for s in rest]
        index=max(range(len(rest)),key=lambda i:gains[i]) if max(gains)>0 else 0
        story=rest.pop(index)
        chosen.append(story)
        regions.add(story["region"])
        fields.add(story["field"])
    return chosen


def branch_a(stories, scale):
    c=Canvas(scale)
    selected=select_stories(stories,32)
    masthead(c,"THE DAILY WORLD","An illustrated record of the day  •  Independently sourced reporting")
    lead=selected[0]
    label(c,24,143,lead["region"]+" / "+lead["field"],13)
    hero_height=c.block((24,165),lead["headline"],468,42,"serif",max_lines=3)
    caption_y=max(300,165+hero_height+15)
    caption_height=c.block((24,caption_y),lead.get("caption", ""),468,17,"sans",max_lines=3)
    if caption_y+caption_height>379:raise ValueError("Lead caption exceeds its panel")
    illustration(c,(516,143,484,230),lead.get("motif","world"))
    c.line([(24,389),(1000,389)],INK,2)
    card(c,selected[1],24,404,476,127,24,True)
    card(c,selected[2],524,404,476,127,24,True)
    rest=selected[3:]
    rows=math.ceil(len(rest)/3)
    row_h=min(51,430/rows)
    for i,s in enumerate(rest):
        col=i//rows
        row=i%rows
        x=24+col*332
        y=550+row*row_h
        label(c,x,y,s["region"],9)
        c.block((x,y+11),s["headline"],310,15,"bold",leading=1.0,max_lines=2)
        if col<2: c.line([(x+320,y),(x+320,y+row_h-4)],RULE,.6)
    footer(c,len(selected),len(set(s["region"] for s in selected)))
    return c,selected


def branch_b(stories, scale):
    c=Canvas(scale,INK)
    selected=select_stories(stories,23)
    masthead(c,"A WORLD IN MOTION","One date. Many places. Events, not predictions.",True)
    c.rect((20,145,1004,554),PAPER)
    # One framed centerpiece with a large focal scene and separated report panels.
    illustration(c,(37,163,549,374),selected[0].get("motif","world"),TEAL)
    c.rect((37,383,586,537),INK)
    label(c,54,397,selected[0]["region"],12,GOLD)
    c.block((54,419),selected[0]["headline"],510,35,"serif",PAPER,max_lines=3)
    for i in (1,2):
        s=selected[i]
        yy=164+(i-1)*190
        illustration(c,(609,yy,147,163),s.get("motif","world"),RED if i==1 else TEAL)
        label(c,773,yy,s["region"],10)
        c.block((773,yy+19),s["headline"],207,21,"bold",max_lines=5)
    rest=selected[3:]
    for i,s in enumerate(rest):
        col=i%4
        row=i//4
        x=24+col*249
        y=579+row*80
        label(c,x,y,s["region"],10,GOLD)
        c.block((x,y+16),s["headline"],228,18,"bold",PAPER,max_lines=3)
        c.line([(x,y+73),(x+228,y+73)],"#49606a",1)
    c.line([(24,992),(1000,992)],GOLD,1)
    c.text((24,1000),"23 REPORTS / PROVISIONAL EDITION / 25 NOVEMBER 2026",10,PAPER,"bold")
    return c,selected


def branch_c(stories, scale):
    c=Canvas(scale,WHITE)
    selected=select_stories(stories,28)
    c.rect((0,0,1024,12),RED)
    label(c,24,28,"THE WORLD / WEDNESDAY",15)
    c.text((24,49),"25 NOVEMBER 2026",53,INK,"bold")
    c.line([(24,119),(1000,119)],INK,3)
    s=selected[0]
    illustration(c,(24,141,283,203),s.get("motif","world"))
    label(c,330,141,s["region"]+" / "+s["field"],13)
    c.block((330,165),s["headline"],658,39,"bold",max_lines=3)
    c.block((330,299),s.get("caption",""),658,16,"sans",max_lines=2)
    c.line([(24,364),(1000,364)],INK,2)
    # Six enlarged regional heads are readable before the compact news digest.
    prominent=[]
    seen={s["region"]}
    for story in selected[1:]:
        if story["region"] not in seen:
            prominent.append(story)
            seen.add(story["region"])
    if len(prominent)!=6: raise ValueError("Clarity layout requires all seven regions")
    for i,story in enumerate(prominent):
        x=24+(i%2)*500
        y=382+(i//2)*81
        c.rect((x,y+2,x+4,y+68),TEAL if i%2 else RED)
        label(c,x+13,y,story["region"],15)
        c.block((x+13,y+22),story["headline"],461,23,"bold",leading=1.05,max_lines=2)
        c.line([(x+13,y+74),(x+474,y+74)],RULE,.7)
    prominent_ids={story["id"] for story in prominent}
    rest=[story for story in selected[1:] if story["id"] not in prominent_ids]
    rows=math.ceil(len(rest)/3)
    if len(rest)!=21 or rows!=7:raise ValueError("C requires three balanced seven-item digest columns")
    for i,story in enumerate(rest):
        x=24+(i//rows)*332
        y=630+(i%rows)*51
        label(c,x,y,story["region"],9)
        c.block((x,y+11),story["headline"],310,16,"bold",leading=1.02,max_lines=2)
        if i//rows<2:c.line([(x+320,y),(x+320,y+46)],RULE,.7)
    footer(c,len(selected),len(set(s["region"] for s in selected)),edition="GLOBAL EDITION")
    return c,selected


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("renders"))
    p.add_argument("--branch",choices=["A","B","C","all"],default="all")
    p.add_argument("--scale",type=int,default=2,choices=[1,2,3])
    p.add_argument("--colors",type=int,default=224)
    args=p.parse_args()
    data=json.loads(args.manifest.read_text())
    stories=data["stories"]
    if data["date"] != "2026-11-25": raise ValueError("Wrong issue date")
    if len({s["id"] for s in stories}) != len(stories): raise ValueError("Duplicate IDs")
    if len(stories)<29: raise ValueError("Branch A requires at least 29 verified reports")
    for s in stories:
        if not s.get("verified") or s.get("eligible_date") != data["date"]:
            raise ValueError("Unverified or ineligible story: "+s["id"])
        if not s.get("sources"): raise ValueError("Missing source evidence")
    args.out.mkdir(parents=True,exist_ok=True)
    result=[]
    for name,fn in [("A",branch_a),("B",branch_b),("C",branch_c)]:
        if args.branch not in (name,"all"): continue
        canvas,selected=fn(stories,args.scale)
        output=args.out/("branch-"+name+".png")
        canvas.save(output,args.colors)
        result.append({"branch":name,"stories":len(selected),"regions":sorted(set(s["region"] for s in selected)),"fields":sorted(set(s["field"] for s in selected)),"bytes":output.stat().st_size,"image":str(output)})
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
