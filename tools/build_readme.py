# Gera os SVGs animados do README do perfil (padrao Dalton Azul).
import base64, io, math, os, re
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

SITE = r"C:/Users/marce/PycharmProjects/Projeto Site"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)
NM = SITE + "/node_modules/"

# ---------- fontes (instancias estaticas, subset por arquivo) ----------
def inst(path, **axes):
    f = TTFont(path)
    return instancer.instantiateVariableFont(f, axes) if axes else f

FONTS = {
    "disp":  inst(NM + "@fontsource-variable/anybody/files/anybody-latin-wdth-normal.woff2", wght=780, wdth=118),
    "dispi": inst(NM + "@fontsource-variable/anybody/files/anybody-latin-wdth-italic.woff2", wght=680, wdth=114),
    "head":  inst(NM + "@fontsource-variable/archivo/files/archivo-latin-wdth-normal.woff2", wght=760, wdth=116),
    "body":  inst(NM + "@fontsource-variable/archivo/files/archivo-latin-wdth-normal.woff2", wght=420, wdth=100),
    "mono":  inst(NM + "@fontsource/jetbrains-mono/files/jetbrains-mono-latin-500-normal.woff2"),
}
FAM = {"disp": "DDisp", "dispi": "DDispI", "head": "DHead", "body": "DBody", "mono": "DMono"}

def measure(font, text, size, ls=0.0):
    f = FONTS[font]
    cmap = f.getBestCmap(); hmtx = f["hmtx"]; upm = f["head"].unitsPerEm
    w = sum(hmtx[cmap.get(ord(c), cmap.get(32))][0] for c in text) * size / upm
    return w + ls * size * len(text)

def embed(used):
    css = []
    for key, chars in used.items():
        f = TTFont()  # copia via buffer
        buf = io.BytesIO(); FONTS[key].save(buf); buf.seek(0)
        f = TTFont(buf)
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern", "liga"]
        opts.name_IDs = []; opts.notdef_outline = True
        s = subset.Subsetter(opts); s.populate(text="".join(sorted(chars)) + " "); s.subset(f)
        out = io.BytesIO(); f.flavor = "woff2"; f.save(out)
        b = base64.b64encode(out.getvalue()).decode()
        css.append(f"@font-face{{font-family:{FAM[key]};src:url(data:font/woff2;base64,{b}) format('woff2')}}")
    return "".join(css)

# ---------- tokens ----------
BG, BG2, BG3 = "#030407", "#07090e", "#0d1018"
WHITE, WHITE2, MUTE, MUTE2 = "#f3f5fa", "#c3c8d4", "#8b91a1", "#545a69"
BLUE, BLUEHI = "#2a54ff", "#7590ff"
EASE = "cubic-bezier(.16,1,.3,1)"
ARROW = "M0 10 L10 0 M3 0 H10 V7"

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class SVG:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.used = {}; self.body = []; self.defs = []; self.css = []
    def t(self, x, y, text, font="body", size=16, fill=WHITE, ls=0.0, anchor="start", cls="", extra=""):
        self.used.setdefault(font, set()).update(text)
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        c = f' class="{cls}"' if cls else ""
        lsp = f' letter-spacing="{ls*size:.2f}"' if ls else ""
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FAM[font]}" font-size="{size}" '
                f'fill="{fill}"{lsp}{a}{c} {extra}>{esc(text)}</text>')
    def add(self, *s): self.body.extend(s)
    def save(self, name, radius=18):
        style = embed(self.used) + "".join(self.css) + \
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}.rw0{opacity:1}.caret{transform:translateX(%spx)}.edge{display:none}}" % getattr(self, "caret0", 0)
        clip = f'<clipPath id="frame"><rect width="{self.w}" height="{self.h}" rx="{radius}"/></clipPath>'
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}" role="img" aria-label="{esc(self.title)}">'
               f'<title>{esc(self.title)}</title><style>{style}</style><defs>{clip}{"".join(self.defs)}</defs>'
               f'<g clip-path="url(#frame)">{"".join(self.body)}</g></svg>')
        open(os.path.join(OUT, name), "w", encoding="utf-8").write(svg)
        print(f"{name:22s} {len(svg)/1024:6.1f} KB")

def wrap(font, text, size, maxw):
    lines, cur = [], ""
    for w in text.split():
        nxt = (cur + " " + w).strip()
        if cur and measure(font, nxt, size) > maxw: lines.append(cur); cur = w
        else: cur = nxt
    return lines + [cur]

def grid(s, gid, step, w, h, op=.045, cx=.5, cy=.5, r=.7):
    s.defs.append(
        f'<pattern id="{gid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
        f'<path d="M{step} 0V{step}H0" fill="none" stroke="#fff" stroke-opacity="{op}"/></pattern>'
        f'<radialGradient id="{gid}m" cx="{cx}" cy="{cy}" r="{r}"><stop offset="0" stop-color="#fff"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        f'<mask id="{gid}k"><rect width="{w}" height="{h}" fill="url(#{gid}m)"/></mask>')
    return f'<rect width="{w}" height="{h}" fill="url(#{gid})" mask="url(#{gid}k)"/>'

def kicker(s, x, y, text, size=12):
    s.defs.append('<linearGradient id="kg" x1="0" x2="1"><stop offset="0" stop-color="#2a54ff" stop-opacity="0"/>'
                  '<stop offset="1" stop-color="#2a54ff"/></linearGradient>'
                  '<filter id="kglow" x="-2" y="-2" width="5" height="5"><feGaussianBlur stdDeviation="2.4"/></filter>')
    return (f'<rect x="{x}" y="{y-size*.42}" width="30" height="1.6" fill="url(#kg)"/>'
            f'<circle cx="{x+34}" cy="{y-size*.35}" r="5" fill="{BLUE}" filter="url(#kglow)"/>'
            f'<circle cx="{x+34}" cy="{y-size*.35}" r="3" fill="{BLUEHI}"/>'
            + s.t(x + 48, y, text.upper(), "mono", size, MUTE, ls=.2))

def two_beat(s, x, y, a, b, size, font_a="disp", font_b="dispi", ls=-.035):
    """Titulo em duas batidas: afirmacao branca + complemento em italico azul."""
    wa = measure(font_a, a + " ", size, ls)
    return (s.t(x, y, a, font_a, size, WHITE, ls=ls) + s.t(x + wa, y, b, font_b, size, BLUEHI, ls=ls * .6)), wa + measure(font_b, b, size, ls * .6)

# ---------- logo D + Edition ----------
def logo_parts():
    mono = open(SITE + "/public/img/dalton/monogram-d.svg", encoding="utf-8").read()
    ed = open(SITE + "/public/img/dalton/edition-sign.svg", encoding="utf-8").read()
    sym = lambda src, i: re.search(rf'<symbol id="{i}"[^>]*>(.*?)</symbol>', src, re.S).group(1)
    return {k: sym(mono, k) for k in ("d-full", "d-side", "d-circuit", "d-glints")} | \
           {k: sym(ed, k) for k in ("edition-fill", "edition-ring", "edition-line")}

L = logo_parts()
PEN = L["edition-line"].replace("<path ", '<path class="pen" ')

def d_mark(s, x, y, scale):
    """D em camadas: laterais, faces com degrade, circuito que se desenha, brilho que varre e Edition a caneta."""
    s.defs.append(
        '<linearGradient id="gface" x1="0" y1="0" x2=".55" y2="1"><stop offset="0" stop-color="#7d95ff"/>'
        '<stop offset=".45" stop-color="#3a5cff"/><stop offset="1" stop-color="#0f2296"/></linearGradient>'
        '<linearGradient id="gside" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2a78"/>'
        '<stop offset="1" stop-color="#070b26"/></linearGradient>'
        '<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<radialGradient id="glint"><stop offset="0" stop-color="#b9c7ff" stop-opacity=".55"/>'
        '<stop offset="1" stop-color="#b9c7ff" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="dclip">{L["d-full"]}</clipPath>'
        '<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter>'
        f'<mask id="pen"><g fill="none" stroke="#fff" stroke-width="110">{PEN}</g></mask>')
    circuit = re.sub(r'<path ', '<path class="trace" ', L["d-circuit"])
    s.css.append(
        "#dface path{fill:url(#gface)}#dside .d-side{fill:url(#gside)}#dside .d-wall{fill:#040615}"
        ".trace{fill:none;stroke:#c3cfff;stroke-width:3;stroke-linecap:round;stroke-dasharray:.18 .82;"
        "stroke-dashoffset:1;opacity:.75;animation:trace 5.5s linear infinite}"
        ".trace:nth-child(3n){animation-delay:-1.8s}.trace:nth-child(3n+1){animation-delay:-3.6s}"
        "@keyframes trace{to{stroke-dashoffset:0}}"
        ".sweep{animation:sweep 7s " + EASE + " infinite}"
        "@keyframes sweep{0%,55%{transform:translateX(-600px) skewX(-18deg)}100%{transform:translateX(1400px) skewX(-18deg)}}"
        "#glints circle{fill:url(#glint);animation:glint 4s ease-in-out infinite alternate}"
        "#glints circle:nth-child(2n){animation-delay:-2s}"
        "@keyframes glint{from{opacity:.25}to{opacity:1}}"
        ".pen{stroke-dasharray:1;stroke-dashoffset:0;animation:pen 9s " + EASE + " infinite}"
        "@keyframes pen{0%{stroke-dashoffset:1}28%,86%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}"
        ".halo{animation:halo 6s ease-in-out infinite alternate;transform-origin:center;transform-box:fill-box}"
        "@keyframes halo{from{opacity:.55;transform:scale(.94)}to{opacity:1;transform:scale(1.04)}}")
    ring = L["edition-ring"]
    return (f'<g transform="translate({x} {y}) scale({scale})">'
            f'<ellipse class="halo" cx="470" cy="470" rx="560" ry="520" fill="url(#halo)"/>'
            f'<g id="dside">{L["d-side"]}</g>'
            f'<g id="dface">{L["d-full"]}</g>'
            f'<g clip-path="url(#dclip)"><g id="glints" filter="url(#soft)">{L["d-glints"]}</g>{circuit}'
            f'<rect class="sweep" x="0" y="-100" width="260" height="1100" fill="url(#sweep)" opacity=".5"/></g>'
            f'<g transform="translate(38 700)"><g mask="url(#pen)"><g fill="{BG}">{L["edition-fill"]}</g>'
            f'<g fill="none" stroke="#e9edff" stroke-linecap="round" stroke-linejoin="round" stroke-width="8.6"'
            f' style="filter:drop-shadow(0 0 6px rgba(117,144,255,.9))">{ring}</g></g></g>'
            f'</g>')

# ================= HERO =================
def hero():
    W, H = 1200, 624
    s = SVG(W, H, "Marcelo Dalton. Desenvolvedor de software: sistemas web, scripts FiveM, SIXM para GTA VI e RPG no navegador.")
    s.defs.append('<radialGradient id="halo"><stop offset="0" stop-color="#2a54ff" stop-opacity=".42"/>'
                  '<stop offset=".6" stop-color="#2a54ff" stop-opacity=".08"/><stop offset="1" stop-color="#2a54ff" stop-opacity="0"/></radialGradient>'
                  '<linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="#030407"/><stop offset=".55" stop-color="#030407" stop-opacity=".85"/>'
                  '<stop offset="1" stop-color="#030407" stop-opacity="0"/></linearGradient>'
                  '<linearGradient id="wordg" x1="0" x2="1"><stop offset="0" stop-color="#9db0ff"/><stop offset="1" stop-color="#4f70ff"/></linearGradient>')
    s.add(f'<rect width="{W}" height="{H}" fill="{BG}"/>', grid(s, "hg", 88, W, H, .05, .72, .45, .75))
    s.add(d_mark(s, 700, 36, 0.46))
    s.add(f'<rect width="640" height="{H}" fill="url(#fadeL)" opacity=".7"/>')
    x = 64
    s.add(kicker(s, x, 100, "Desenvolvedor de software", 12.5))
    s.add(s.t(x, 150, "Olá, eu sou", "body", 22, WHITE2, cls="up u1"))
    s.add(s.t(x, 250, "Marcelo", "disp", 106, WHITE, ls=-.05, cls="up u2"))
    wd = measure("disp", "Dalton", 106, -.05)
    s.add(f'<g class="up u3">{s.t(x, 348, "Dalton", "disp", 106, WHITE, ls=-.05)}'
          f'<rect x="{x+wd+6:.1f}" y="330" width="17" height="17" fill="{BLUE}"/></g>')
    # palavra que gira
    size = 38; y = 422
    pre = "Desenvolvo "
    s.add(s.t(x, y, pre, "disp", size, WHITE, ls=-.03, cls="up u4"))
    words = ["scripts FiveM.", "sistemas web.", "scripts de GTA VI.", "RPG no navegador."]
    wx = x + measure("disp", pre, size, -.03)
    n, cyc = len(words), 12
    s.defs.append(f'<clipPath id="rotc"><rect x="{wx-4}" y="{y-size}" width="560" height="{size*1.3}"/></clipPath>')
    g = []
    for i, w in enumerate(words):
        g.append(s.t(wx, y, w, "dispi", size, "url(#wordg)", ls=-.02, cls=f"rw rw{i}", extra=f'style="animation-delay:{i*cyc/n - cyc:.2f}s"'))
    widths = [measure("dispi", w, size, -.02) for w in words]
    s.caret0 = round(widths[0] + 10, 1)
    seg = 100 / n
    kf = []
    for i, wv in enumerate(widths):
        kf.append(f"{i*seg:.2f}%,{(i+1)*seg-.01:.2f}%{{transform:translateX({wv+10:.1f}px)}}")
    s.css.append(
        f".rw{{opacity:0;animation:rw {cyc}s {EASE} infinite}}"
        f"@keyframes rw{{0%{{opacity:0;transform:translateY(34px)}}3%,22%{{opacity:1;transform:none}}25%,100%{{opacity:0;transform:translateY(-30px)}}}}"
        f".caret{{animation:blink 1s steps(1) infinite,cx {cyc}s steps(1) infinite}}"
        f"@keyframes blink{{50%{{opacity:0}}}}@keyframes cx{{{''.join(kf)}}}"
        f".up{{animation:up 1.4s {EASE} both}}.u1{{animation-delay:.1s}}.u2{{animation-delay:.2s}}.u3{{animation-delay:.3s}}.u4{{animation-delay:.45s}}.u5{{animation-delay:.6s}}"
        f"@keyframes up{{from{{opacity:0;transform:translateY(26px)}}to{{opacity:1;transform:none}}}}")
    s.add(f'<g class="up u4"><g clip-path="url(#rotc)">{"".join(g)}</g>'
          f'<g class="caret"><rect x="{wx}" y="{y-size*.72}" width="2.5" height="{size*.78}" fill="{WHITE}"/></g></g>')
    lede = ["Formado em Sistemas de Informação, há mais de 5 anos", "colocando software no ar. Do banco de dados à tela."]
    s.add(f'<g class="up u5">' + "".join(s.t(x, 470 + i*27, l, "body", 18, WHITE2) for i, l in enumerate(lede)) + "</g>")
    # faixa de fatos
    facts = [("5+ anos", "em produção"), ("Formado", "sistemas de informação"), ("100%", "código próprio")]
    fx = x; fy = 576
    s.add(f'<line x1="{x}" x2="{W-64}" y1="{fy-44}" y2="{fy-44}" stroke="#fff" stroke-opacity=".08"/>')
    for i, (a, b) in enumerate(facts):
        s.add(s.t(fx, fy - 8, a, "head", 22, WHITE, ls=-.02), s.t(fx, fy + 12, b.upper(), "mono", 9.5, MUTE2, ls=.16))
        fw = max(measure("head", a, 22), measure("mono", b.upper(), 9.5, .16)) + 44
        if i < 2: s.add(f'<line x1="{fx+fw-22}" x2="{fx+fw-22}" y1="{fy-26}" y2="{fy+14}" stroke="#fff" stroke-opacity=".12"/>')
        fx += fw
    s.css.append(".live{animation:live 1.6s ease-in-out infinite}@keyframes live{50%{opacity:.25}}")
    s.add(f'<circle class="live" cx="{W-300}" cy="{fy-3}" r="3.5" fill="{BLUE}"/>',
          s.t(W - 288, fy + 1, "DEVDALTONEDITION.COM", "mono", 10.5, MUTE, ls=.16),
          f'<path d="{ARROW}" transform="translate({W-76} {fy-8})" stroke="{BLUEHI}" stroke-width="1.8" fill="none" stroke-linecap="round"/>')
    s.save("hero.svg")

# ================= CABECALHOS DE SECAO =================
def header(name, kick, a, b, lede=None):
    W = 1200; H = 184 if lede else 150
    s = SVG(W, H, f"{kick}. {a} {b}")
    s.add(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    s.add(kicker(s, 34, 40, kick, 12))
    size = 64
    while two_beat(s, 32, 0, a, b, size)[1] > 1130: size -= 1
    t, _ = two_beat(s, 32, 118, a, b, size)
    s.add(f'<g class="up">{t}</g>')
    if lede: s.add(s.t(34, 162, lede, "body", 19, WHITE2))
    s.css.append(f".up{{animation:up 1.4s {EASE} both .15s}}@keyframes up{{from{{opacity:0;transform:translateY(22px)}}to{{opacity:1;transform:none}}}}")
    s.save(name)

# ================= CARTOES (frentes) =================
def card_shell(s, W, H, num, chip, live=True):
    s.defs.append('<linearGradient id="cg" x1="0" y1="0" x2=".6" y2="1"><stop offset="0" stop-color="#2a54ff" stop-opacity=".1"/>'
                  '<stop offset=".45" stop-color="#2a54ff" stop-opacity="0"/></linearGradient>')
    s.css.append(".live{animation:live 1.6s ease-in-out infinite}@keyframes live{50%{opacity:.2}}"
                 ".edge{stroke-dasharray:.12 .88;animation:edge 9s linear infinite}@keyframes edge{to{stroke-dashoffset:-1}}")
    cw = measure("mono", chip.upper(), 10, .14) + (38 if live else 26)
    return (f'<rect width="{W}" height="{H}" fill="{BG2}"/><rect width="{W}" height="{H}" fill="url(#cg)"/>'
            f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="#fff" stroke-opacity=".08"/>'
            f'<rect class="edge" pathLength="1" x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="{BLUEHI}" stroke-opacity=".7" stroke-width="1.4"/>'
            + s.t(26, 38, num, "mono", 11, MUTE2, ls=.14)
            + f'<rect x="{W-26-cw}" y="22" width="{cw}" height="26" rx="13" fill="#fff" fill-opacity=".04" stroke="#fff" stroke-opacity=".12"/>'
            + (f'<circle class="live" cx="{W-26-cw+15}" cy="35" r="3.2" fill="{BLUEHI}"/>' if live else "")
            + s.t(W - 26 - cw + (26 if live else 13), 39, chip.upper(), "mono", 10, WHITE2, ls=.14))

def viz_box(s, x, y, w, h):
    s.defs.append('<pattern id="vg" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0V22H0" fill="none" stroke="#fff" stroke-opacity=".05"/></pattern>'
                  '<radialGradient id="vr" cx=".5" cy="1" r=".8"><stop offset="0" stop-color="#2a54ff" stop-opacity=".22"/><stop offset="1" stop-color="#2a54ff" stop-opacity="0"/></radialGradient>')
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{BG3}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="url(#vg)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="url(#vr)"/>'
            f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" rx="12" fill="none" stroke="#fff" stroke-opacity=".06"/>')

def card_text(s, W, H, title, line, tags, cta):
    out = [s.t(26, H - 150, title, "head", 30, WHITE, ls=-.03)]
    for i, l in enumerate(wrap("body", line, 16.5, W - 70)):
        out.append(s.t(26, H - 116 + i * 23, l, "body", 16.5, WHITE2))
    tx = 26
    for tg in tags:
        tw = measure("mono", tg.upper(), 10, .12) + 22
        out.append(f'<rect x="{tx}" y="{H-66}" width="{tw}" height="24" rx="12" fill="none" stroke="#fff" stroke-opacity=".13"/>'
                   + s.t(tx + 11, H - 50, tg.upper(), "mono", 10, MUTE, ls=.12))
        tx += tw + 8
    # link com verbo
    out.append(s.t(26, H - 18, cta, "head", 14, WHITE, ls=-.01)
               + f'<path d="{ARROW}" transform="translate({30+measure("head", cta, 14, -.01):.1f} {H-29}) scale(.9)" stroke="{BLUEHI}" stroke-width="2" fill="none" stroke-linecap="round"/>'
               + f'<rect x="26" y="{H-11}" width="{measure("head", cta, 14, -.01)+18:.1f}" height="1.4" fill="{BLUE}" class="ul"/>')
    s.css.append(f".ul{{transform-origin:left;animation:ul 4s {EASE} infinite}}@keyframes ul{{0%{{transform:scaleX(0)}}40%,80%{{transform:scaleX(1);opacity:1}}100%{{transform:scaleX(1);opacity:0}}}}")
    return "".join(out)

W_C, H_C = 600, 440
VX, VY, VW, VH = 26, 64, 548, 170

def card_web():
    s = SVG(W_C, H_C, "01. Sistemas web: sites, painéis e APIs sob medida para o seu negócio.")
    s.add(card_shell(s, W_C, H_C, "01", "Sob medida"), viz_box(s, VX, VY, VW, VH))
    bx, by = VX + 28, VY + 20
    s.add(f'<rect x="{bx}" y="{by}" width="300" height="130" rx="9" fill="{BG2}" stroke="#fff" stroke-opacity=".1"/>'
          + "".join(f'<circle cx="{bx+14+i*11}" cy="{by+12}" r="3" fill="#fff" fill-opacity=".18"/>' for i in range(3))
          + f'<rect x="{bx+50}" y="{by+7}" width="200" height="10" rx="5" fill="#fff" fill-opacity=".06"/>')
    rows = [(.9, BLUE), (.55, "#fff"), (.72, "#fff"), (.4, "#fff")]
    for i, (f, c) in enumerate(rows):
        op = "1" if c == BLUE else ".14"
        s.add(f'<rect class="bar" style="animation-delay:{i*.35}s" x="{bx+16}" y="{by+36+i*22}" width="{268*f:.0f}" height="9" rx="4.5" fill="{c}" fill-opacity="{op}"/>')
    # terminal de requisicoes
    tx, ty = bx + 318, by
    s.add(f'<rect x="{tx}" y="{ty}" width="174" height="130" rx="9" fill="#05070c" stroke="#fff" stroke-opacity=".1"/>')
    reqs = [("GET", "/api/v1/produtos", "200"), ("POST", "/auth/login", "200"), ("GET", "/api/v1/pedidos", "200"), ("POST", "/auth/login", "429")]
    for i, (m, p, c) in enumerate(reqs):
        col = BLUEHI if c == "200" else "#ff6b81"
        s.add(f'<g class="req" style="animation-delay:{i*1.1}s">'
              + s.t(tx + 12, ty + 26 + i * 27, m, "mono", 9.5, MUTE) + s.t(tx + 46, ty + 26 + i * 27, p, "mono", 9.5, WHITE2)
              + s.t(tx + 162, ty + 26 + i * 27, c, "mono", 9.5, col, anchor="end") + "</g>")
    s.css.append(f".bar{{transform-box:fill-box;transform-origin:left;animation:bar 4.4s {EASE} infinite}}"
                 "@keyframes bar{0%{transform:scaleX(.08)}35%,100%{transform:scaleX(1)}}"
                 ".req{animation:req 4.4s steps(1) infinite}@keyframes req{0%{opacity:0}8%,100%{opacity:1}}")
    s.add(card_text(s, W_C, H_C, "Sistemas web", "Sites, painéis e APIs sob medida para o seu negócio.",
                    ["Front e back", "Login seguro", "Banco de dados"], "Ver projetos web"))
    s.save("card-web.svg")

def card_fivem():
    s = SVG(W_C, H_C, "02. Scripts FiveM: celular, banco, imobiliária e justiça para servidores de roleplay.")
    s.add(card_shell(s, W_C, H_C, "02", "Disponível"), viz_box(s, VX, VY, VW, VH))
    # celular com grade de apps que acende em sequencia
    px, py = VX + 40, VY + 14
    s.add(f'<rect x="{px}" y="{py}" width="92" height="170" rx="16" fill="#05070c" stroke="#fff" stroke-opacity=".18" stroke-width="1.5"/>'
          f'<rect x="{px+33}" y="{py+7}" width="26" height="6" rx="3" fill="#fff" fill-opacity=".14"/>')
    k = 0
    for r in range(5):
        for c in range(4):
            s.add(f'<rect class="app" style="animation-delay:{k*.12:.2f}s" x="{px+10+c*19}" y="{py+24+r*20}" width="14" height="14" rx="4" fill="{BLUEHI}"/>')
            k += 1
    # resmon
    rx, ry = px + 130, py + 8
    s.add(s.t(rx, ry + 12, "RESMON", "mono", 10, MUTE, ls=.16), s.t(rx + 330, ry + 12, "AO VIVO", "mono", 10, BLUEHI, ls=.16, anchor="end"))
    for i, nm in enumerate(["dtCelular", "dtDaltawon", "dtImob", "dtJurídico"]):
        yy = ry + 44 + i * 30
        s.add(s.t(rx, yy, nm, "mono", 11.5, WHITE2),
              f'<rect x="{rx+120}" y="{yy-5}" width="130" height="2" fill="#fff" fill-opacity=".08"/>'
              f'<rect class="blip" style="animation-delay:{i*.5}s" x="{rx+120}" y="{yy-6}" width="4" height="4" rx="2" fill="{BLUEHI}"/>',
              s.t(rx + 330, yy, "0.00 ms", "mono", 11.5, WHITE, anchor="end"))
    s.css.append(".app{opacity:.1;animation:app 3.6s ease-in-out infinite}@keyframes app{0%,100%{opacity:.1}12%{opacity:.95}40%{opacity:.25}}"
                 ".blip{animation:blip 2.4s " + EASE + " infinite}@keyframes blip{0%{transform:translateX(0);opacity:0}10%{opacity:1}100%{transform:translateX(126px);opacity:0}}")
    s.add(card_text(s, W_C, H_C, "Scripts FiveM", "Celular, banco, imobiliária e justiça para servidores de roleplay.",
                    ["Lua e NUI", "0.00 ms em repouso", "Interface própria"], "Entrar na loja"))
    s.save("card-fivem.svg")

def card_sixm():
    s = SVG(W_C, H_C, "03. SIXM, GTA VI: scripts para os primeiros servidores de GTA VI no PC.")
    s.add(card_shell(s, W_C, H_C, "03", "Pré-lançamento"), viz_box(s, VX, VY, VW, VH))
    # horizonte da cidade com sol e varredura
    s.defs.append(f'<clipPath id="vc"><rect x="{VX}" y="{VY}" width="{VW}" height="{VH}" rx="12"/></clipPath>'
                  '<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9db0ff"/><stop offset="1" stop-color="#2a54ff" stop-opacity=".1"/></linearGradient>'
                  '<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7590ff" stop-opacity="0"/><stop offset="1" stop-color="#7590ff" stop-opacity=".35"/></linearGradient>')
    base = VY + VH - 26
    sun = f'<circle cx="{VX+VW/2}" cy="{base}" r="70" fill="url(#sun)" opacity=".55"/>'
    stripes = "".join(f'<rect x="{VX+VW/2-72}" y="{base-54+i*12}" width="144" height="{2+i*.8:.1f}" fill="{BG3}"/>' for i in range(5))
    import random; random.seed(6)
    bld = []; xx = VX + 10
    while xx < VX + VW - 20:
        w = random.randint(16, 34); h = random.randint(22, 92)
        bld.append(f'<rect x="{xx}" y="{base-h}" width="{w}" height="{h}" fill="#05070c" stroke="{BLUEHI}" stroke-opacity=".35"/>')
        for wy in range(base - h + 8, base - 6, 11):
            if random.random() < .35:
                bld.append(f'<rect class="win" style="animation-delay:{random.random()*4:.2f}s" x="{xx+4}" y="{wy}" width="{w-8}" height="2" fill="{BLUEHI}"/>')
        xx += w + random.randint(2, 7)
    palms = "".join(f'<path d="M{px} {base} q-2 -30 3 -52 M{px+3} {base-52} q-16 -2 -24 10 M{px+3} {base-52} q14 -4 24 8 M{px+3} {base-52} q-4 -14 -16 -16 M{px+3} {base-52} q8 -12 20 -10" fill="none" stroke="{WHITE2}" stroke-opacity=".6" stroke-width="2" stroke-linecap="round"/>' for px in (VX + 60, VX + VW - 70))
    s.add(f'<g clip-path="url(#vc)">{sun}{stripes}{"".join(bld)}{palms}'
          f'<rect x="{VX}" y="{base}" width="{VW}" height="26" fill="#05070c"/>'
          + "".join(f'<line x1="{VX+VW/2}" y1="{base}" x2="{VX+VW/2+(i-6)*70}" y2="{VY+VH}" stroke="{BLUEHI}" stroke-opacity=".25"/>' for i in range(13))
          + f'<rect class="scan" x="{VX}" y="{VY}" width="{VW}" height="40" fill="url(#scan)"/></g>'
          + s.t(VX + 16, VY + 24, "PC · GTA VI", "mono", 10, WHITE2, ls=.16))
    s.css.append(".scan{animation:scan 4s linear infinite}@keyframes scan{from{transform:translateY(-40px)}to{transform:translateY(170px)}}"
                 ".win{animation:win 3s steps(1) infinite}@keyframes win{50%{opacity:.15}}")
    s.add(card_text(s, W_C, H_C, "SIXM · GTA VI", "Scripts para os primeiros servidores de GTA VI no PC.",
                    ["Pré-lançamento", "Demos jogáveis"], "Jogar as demos"))
    s.save("card-sixm.svg")

def card_rpg():
    s = SVG(W_C, H_C, "04. RPG no navegador: ficha, mapa e dado com física. A mesa inteira online.")
    s.add(card_shell(s, W_C, H_C, "04", "Em breve", live=False), viz_box(s, VX, VY, VW, VH))
    # d20 girando + ficha
    cx, cy, R = VX + 120, VY + VH / 2, 58
    hexp = " ".join(f"{cx+R*math.cos(math.radians(90+60*i)):.1f},{cy-R*math.sin(math.radians(90+60*i)):.1f}" for i in range(6))
    tri = " ".join(f"{cx+R*.62*math.cos(math.radians(90+120*i)):.1f},{cy-R*.62*math.sin(math.radians(90+120*i)):.1f}" for i in range(3))
    P = [(cx+R*math.cos(math.radians(90+60*i)), cy-R*math.sin(math.radians(90+60*i))) for i in range(6)]
    T = [(cx+R*.62*math.cos(math.radians(90+120*i)), cy-R*.62*math.sin(math.radians(90+120*i))) for i in range(3)]
    links = [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2), (4, 2), (4, 0), (5, 0)]
    lines = "".join(f'<line x1="{P[a][0]:.1f}" y1="{P[a][1]:.1f}" x2="{T[b][0]:.1f}" y2="{T[b][1]:.1f}"/>' for a, b in links)
    nums = "".join(f'<g class="dn" style="animation-delay:{i*.5}s">{s.t(cx, cy+9, n, "disp", 26, WHITE, anchor="middle")}</g>' for i, n in enumerate(["20"]))
    s.add(f'<ellipse cx="{cx}" cy="{cy+R+8}" rx="46" ry="6" fill="{BLUE}" opacity=".35"/>'
          f'<g class="die"><polygon points="{hexp}" fill="#0c1640" stroke="{BLUEHI}" stroke-width="2"/>'
          f'<g stroke="{BLUEHI}" stroke-opacity=".55" stroke-width="1.4">{lines}</g>'
          f'<polygon points="{tri}" fill="#1c2f9e" stroke="{BLUEHI}" stroke-width="1.6"/>{nums}</g>')
    # ficha
    fx, fy = VX + 250, VY + 22
    s.add(f'<rect x="{fx}" y="{fy}" width="270" height="126" rx="9" fill="{BG2}" stroke="#fff" stroke-opacity=".1"/>'
          + s.t(fx + 14, fy + 24, "FICHA · NÍVEL 7", "mono", 10, MUTE, ls=.14))
    for i, (lb, v) in enumerate([("VIDA", .8), ("MANA", .55), ("VIGOR", .68)]):
        yy = fy + 50 + i * 26
        s.add(s.t(fx + 14, yy + 4, lb, "mono", 9.5, WHITE2, ls=.1),
              f'<rect x="{fx+74}" y="{yy-4}" width="180" height="7" rx="3.5" fill="#fff" fill-opacity=".07"/>'
              f'<rect class="hp" style="animation-delay:{i*.4}s" x="{fx+74}" y="{yy-4}" width="{180*v:.0f}" height="7" rx="3.5" fill="{BLUE if i==0 else BLUEHI}"/>')
    s.css.append(f".die{{transform-box:fill-box;transform-origin:center;animation:die 3s {EASE} infinite}}"
                 "@keyframes die{0%{transform:rotate(0) scale(.9)}40%{transform:rotate(360deg) scale(1)}100%{transform:rotate(360deg) scale(1)}}"
                 ".dn{animation:dn 3s steps(1) infinite}@keyframes dn{0%{opacity:0}40%,100%{opacity:1}}"
                 f".hp{{transform-box:fill-box;transform-origin:left;animation:hp 5s {EASE} infinite alternate}}@keyframes hp{{from{{transform:scaleX(.35)}}to{{transform:scaleX(1)}}}}")
    s.add(card_text(s, W_C, H_C, "RPG no navegador", "Ficha, mapa e dado com física. A mesa inteira online.",
                    ["Tempo real", "22 módulos", "Em breve"], "Ver a mesa"))
    s.save("card-rpg.svg")

# ================= PROVAS =================
def proofs():
    W, H = 1200, 330
    s = SVG(W, H, "Por que confiar: teste antes de pagar, 0.00 ms em repouso, código 100% próprio, seus dados protegidos.")
    s.add(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    s.defs.append('<linearGradient id="cg" x1="0" y1="0" x2=".6" y2="1"><stop offset="0" stop-color="#2a54ff" stop-opacity=".1"/>'
                  '<stop offset=".45" stop-color="#2a54ff" stop-opacity="0"/></linearGradient>')
    tw, gap = (W - 3 * 14) / 4, 14
    items = [("01", "Teste antes de pagar", "Os sistemas rodam dentro do site. Abra, toque, jogue."),
             ("02", "0.00 ms em repouso", "Script parado não pesa no seu servidor."),
             ("03", "Código 100% próprio", "Nada de template revendido. Cada linha tem dono."),
             ("04", "Seus dados protegidos", "Login com token, limite de tentativas e LGPD.")]
    for i, (n, t, d) in enumerate(items):
        x = i * (tw + gap)
        s.add(f'<g transform="translate({x:.1f} 0)">'
              f'<rect width="{tw:.1f}" height="{H}" rx="18" fill="{BG2}"/><rect width="{tw:.1f}" height="{H}" rx="18" fill="url(#cg)"/>'
              f'<rect x=".5" y=".5" width="{tw-1:.1f}" height="{H-1}" rx="18" fill="none" stroke="#fff" stroke-opacity=".08"/>'
              + viz_box(s, 16, 16, tw - 32, 150) + proof_viz(s, i, 16, 16, tw - 32, 150)
              + s.t(20, 206, n, "mono", 10.5, BLUEHI, ls=.14) + s.t(20, 236, t, "head", min(21, 21 * (tw - 40) / measure("head", t, 21, -.03)), WHITE, ls=-.03)
              + "".join(s.t(20, 266 + k * 21, l, "body", 14.5, WHITE2) for k, l in enumerate(wrap("body", d, 14.5, tw - 44)))
              + "</g>")
    s.css.append(f".ok{{animation:ok 6s {EASE} infinite}}@keyframes ok{{0%,30%{{opacity:0;transform:translateY(6px)}}40%,90%{{opacity:1;transform:none}}100%{{opacity:0}}}}"
                 ".tap{transform-box:fill-box;transform-origin:center;animation:tap 2.4s ease-out infinite}@keyframes tap{0%{transform:scale(.2);opacity:.9}100%{transform:scale(2.4);opacity:0}}"
                 ".cur{animation:cur 2.4s " + EASE + " infinite}@keyframes cur{0%{transform:translate(30px,26px)}35%,100%{transform:none}}"
                 ".ln{transform-box:fill-box;transform-origin:left;animation:ln 6s " + EASE + " infinite}@keyframes ln{0%{transform:scaleX(0)}25%,100%{transform:scaleX(1)}}"
                 ".sc{animation:sc 3s linear infinite}@keyframes sc{from{transform:translateY(0)}to{transform:translateY(96px)}}"
                 ".blip{animation:blip 2.4s " + EASE + " infinite}@keyframes blip{0%{transform:translateX(0);opacity:0}10%{opacity:1}100%{transform:translateX(96px);opacity:0}}")
    s.save("proofs.svg", radius=0)

def proof_viz(s, i, x, y, w, h):
    cx = x + w / 2
    if i == 0:
        return (f'<rect x="{cx-38}" y="{y+18}" width="76" height="120" rx="12" fill="#05070c" stroke="#fff" stroke-opacity=".2"/>'
                f'<rect x="{cx-26}" y="{y+40}" width="52" height="8" rx="4" fill="{BLUE}"/>'
                + "".join(f'<rect x="{cx-26}" y="{y+56+k*12}" width="{[40,30,46][k]}" height="5" rx="2.5" fill="#fff" fill-opacity=".14"/>' for k in range(3))
                + f'<circle class="tap" cx="{cx+8}" cy="{y+96}" r="10" fill="none" stroke="{BLUEHI}" stroke-width="2"/>'
                f'<g class="cur"><path d="M{cx+8} {y+96} l0 22 l6 -6 l8 12 l4 -2 l-7 -12 l9 0 z" fill="{WHITE}" stroke="{BG}" stroke-width="1.2"/></g>')
    if i == 1:
        out = [s.t(x + 16, y + 26, "RESMON", "mono", 9, MUTE, ls=.14), s.t(x + w - 16, y + 26, "AO VIVO", "mono", 9, BLUEHI, ls=.14, anchor="end")]
        for k, nm in enumerate(["dtCelular", "dtDaltawon", "dtImob"]):
            yy = y + 60 + k * 30
            out.append(s.t(x + 16, yy, nm, "mono", 10.5, WHITE2)
                       + f'<rect x="{x+100}" y="{yy-5}" width="100" height="2" fill="#fff" fill-opacity=".08"/>'
                       f'<rect class="blip" style="animation-delay:{k*.6}s" x="{x+100}" y="{yy-6}" width="4" height="4" rx="2" fill="{BLUEHI}"/>'
                       + s.t(x + w - 16, yy, "0.00 ms", "mono", 10.5, WHITE, anchor="end"))
        return "".join(out)
    if i == 2:
        ws = [.55, .8, .35, .7, .5]
        out = [f'<rect class="ln" style="animation-delay:{k*.25}s" x="{x+22+(12 if k in (1,2,3) else 0)}" y="{y+24+k*18}" width="{(w-70)*ws[k]:.0f}" height="6" rx="3" fill="{BLUE if k==1 else "#fff"}" fill-opacity="{1 if k==1 else .16}"/>' for k in range(5)]
        cw = measure("mono", "REVISADO", 9, .14) + 30
        out.append(f'<g class="ok"><rect x="{x+w-cw-14}" y="{y+h-36}" width="{cw}" height="22" rx="11" fill="#0c1640" stroke="{BLUEHI}" stroke-opacity=".6"/>'
                   f'<path d="M{x+w-cw} {y+h-25} l3 3 l6 -6" stroke="{BLUEHI}" stroke-width="1.8" fill="none" stroke-linecap="round"/>'
                   + s.t(x + w - cw + 13, y + h - 21, "REVISADO", "mono", 9, BLUEHI, ls=.14) + "</g>")
        return "".join(out)
    # escudo com cadeado e varredura
    s.defs.append(f'<clipPath id="shc"><path d="M{cx} {y+24} l40 14 v30 c0 28 -18 44 -40 54 c-22 -10 -40 -26 -40 -54 v-30 z"/></clipPath>'
                  '<linearGradient id="scan2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7590ff" stop-opacity="0"/><stop offset="1" stop-color="#7590ff" stop-opacity=".45"/></linearGradient>')
    return (f'<path d="M{cx} {y+24} l40 14 v30 c0 28 -18 44 -40 54 c-22 -10 -40 -26 -40 -54 v-30 z" fill="#0a1236" stroke="{BLUEHI}" stroke-width="1.8"/>'
            f'<g clip-path="url(#shc)"><rect class="sc" x="{cx-44}" y="{y}" width="88" height="30" fill="url(#scan2)"/></g>'
            f'<rect x="{cx-12}" y="{y+68}" width="24" height="19" rx="3" fill="none" stroke="{WHITE}" stroke-width="1.8"/>'
            f'<path d="M{cx-7} {y+68} v-6 a7 7 0 0 1 14 0 v6" fill="none" stroke="{WHITE}" stroke-width="1.8"/>')

# ================= STACK =================
def stack():
    W = 1200
    rows = [("Back", ["Node.js", "Express", "TypeScript", "C#", "Python", "Zod", "JWT"]),
            ("Front", ["JavaScript", "React", "Vite", "GSAP", "Three.js", "WebGL"]),
            ("Jogo", ["Lua", "FiveM", "NUI", "Blender", "Sollumz"]),
            ("Dados", ["MySQL", "WebSocket", "SQLite"])]
    H = 40 + len(rows) * 62
    s = SVG(W, H, "Stack: " + "; ".join(f"{a}: {', '.join(b)}" for a, b in rows))
    s.add(f'<rect width="{W}" height="{H}" fill="{BG2}"/>',
          f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="#fff" stroke-opacity=".08"/>')
    s.defs.append('<linearGradient id="lite" x1="0" x2="1"><stop offset="0" stop-color="#2a54ff" stop-opacity="0"/>'
                  '<stop offset=".5" stop-color="#2a54ff" stop-opacity=".22"/><stop offset="1" stop-color="#2a54ff" stop-opacity="0"/></linearGradient>')
    for r, (lab, items) in enumerate(rows):
        y = 34 + r * 62
        s.add(s.t(32, y + 28, f"0{r+1}", "mono", 10.5, MUTE2, ls=.14), s.t(72, y + 28, lab.upper(), "mono", 11, BLUEHI, ls=.18))
        x = 200
        for k, it in enumerate(items):
            w = measure("head", it, 17, -.02) + 40
            s.add(f'<g class="chip" style="animation-delay:{(r*7+k)*.18:.2f}s"><rect x="{x}" y="{y+6}" width="{w:.0f}" height="36" rx="18" fill="#fff" fill-opacity=".03" stroke="#fff" stroke-opacity=".13"/>'
                  f'<circle cx="{x+16}" cy="{y+24}" r="3" fill="{BLUE}"/>' + s.t(x + 26, y + 30, it, "head", 17, WHITE, ls=-.02) + "</g>")
            x += w + 10
        if r < len(rows) - 1:
            s.add(f'<line x1="32" x2="{W-32}" y1="{y+56}" y2="{y+56}" stroke="#fff" stroke-opacity=".06"/>')
    s.add(f'<rect class="lite" x="-300" y="0" width="300" height="{H}" fill="url(#lite)"/>')
    s.css.append(f".lite{{animation:lite 6s {EASE} infinite}}@keyframes lite{{0%{{transform:translateX(0)}}60%,100%{{transform:translateX(1800px)}}}}"
                 f".chip{{animation:chip 1s {EASE} both}}@keyframes chip{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}")
    s.save("stack.svg")

# ================= BOTOES =================
def button(name, label, icon, primary, h=64, size=19, label_alt=None):
    iw = 26 if icon else 0
    tw = measure("head", label, size, -.01)
    w = 30 + (iw + 10 if icon else 0) + tw + 16 + 12 + 30
    s = SVG(int(w), h, label_alt or label)
    fill = BLUE if primary else "#0b0d13"
    s.defs.append('<linearGradient id="bs" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    s.add(f'<rect width="{w:.0f}" height="{h}" rx="{h/2}" fill="{fill}"/>',
          "" if primary else f'<rect x=".75" y=".75" width="{w-1.5:.0f}" height="{h-1.5}" rx="{h/2-1}" fill="none" stroke="#fff" stroke-opacity=".2" stroke-width="1.5"/>')
    if primary:
        s.add(f'<rect class="bs" x="-120" y="0" width="100" height="{h}" fill="url(#bs)"/>')
        s.css.append(f".bs{{animation:bs 3.6s {EASE} infinite}}@keyframes bs{{0%{{transform:translateX(0) skewX(-20deg)}}55%,100%{{transform:translateX({w+260:.0f}px) skewX(-20deg)}}}}")
    x = 30
    if icon:
        s.add(f'<g transform="translate({x} {h/2-11}) scale(.92)" fill="none" stroke="{WHITE if primary else BLUEHI}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{icon}</g>')
        x += iw + 10
    s.add(s.t(x, h / 2 + size * .36, label, "head", size, WHITE, ls=-.01))
    s.add(f'<path d="{ARROW}" transform="translate({x+tw+16:.0f} {h/2-6}) scale(1.1)" stroke="{WHITE if primary else BLUEHI}" stroke-width="1.8" fill="none" stroke-linecap="round"/>')
    s.save(name, radius=h / 2)

I_DISCORD = '<path d="M18.6 5.4A16 16 0 0 0 14.6 4l-.5 1a15 15 0 0 0-4.2 0l-.5-1a16 16 0 0 0-4 1.4C2.9 9.2 2.2 12.9 2.5 16.6a16 16 0 0 0 4.9 2.5l1-1.6c-.6-.2-1.1-.5-1.6-.8M16.6 16.7c-.5.3-1 .6-1.6.8l1 1.6a16 16 0 0 0 4.9-2.5c.4-4.3-.6-8-2.3-11.2M7.3 16a11 11 0 0 0 9.4 0"/><circle cx="9" cy="12.3" r="1.4"/><circle cx="15" cy="12.3" r="1.4"/>'
I_MAIL = '<rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="M3 6.5l9 6.5 9-6.5"/>'
I_GLOBE = '<circle cx="12" cy="12" r="9.5"/><path d="M2.5 12h19M12 2.5c3 3.2 3 15.8 0 19M12 2.5c-3 3.2-3 15.8 0 19"/>'
I_INSTA = '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.3" cy="6.7" r=".6"/>'
I_IN = '<rect x="3" y="3" width="18" height="18" rx="3.5"/><path d="M7.5 10.5v6M7.5 7.5v.01M11.5 16.5v-6M11.5 13c0-1.6 1.1-2.6 2.5-2.6s2.5 1 2.5 2.6v3.5"/>'

# ================= RODAPE =================
def footer():
    W, H = 1200, 250
    s = SVG(W, H, "Dalton Edition. Resposta direta de quem escreve o código.")
    s.add(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    s.defs.append('<radialGradient id="fl" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#7590ff"/><stop offset="1" stop-color="#2a54ff" stop-opacity="0"/></radialGradient>'
                  f'<mask id="fm"><rect width="{W}" height="{H}" fill="#000"/><circle class="fl" cx="0" cy="110" r="260" fill="url(#fl)"/></mask>')
    word = s.t(W / 2, 176, "DALTON", "disp", 200, "none", ls=-.04, anchor="middle",
               extra='textLength="1110" lengthAdjust="spacingAndGlyphs"')
    s.add(f'<g stroke="#fff" stroke-opacity=".14" stroke-width="1.3">{word}</g>',
          f'<g stroke="{BLUEHI}" stroke-width="2" mask="url(#fm)" style="filter:drop-shadow(0 0 8px rgba(42,84,255,.8))">{word}</g>')
    s.css.append(f".fl{{animation:fl 8s {EASE} infinite alternate}}@keyframes fl{{from{{transform:translateX(120px)}}to{{transform:translateX(1080px)}}}}")
    s.add(f'<line x1="40" x2="{W-40}" y1="206" y2="206" stroke="#fff" stroke-opacity=".08"/>',
          s.t(40, 232, "RESPOSTA DIRETA DE QUEM ESCREVE O CÓDIGO.", "mono", 10.5, MUTE, ls=.16),
          s.t(W - 40, 232, "BELO HORIZONTE · MG · BRASIL", "mono", 10.5, MUTE2, ls=.16, anchor="end"))
    s.save("footer.svg")

if __name__ == "__main__":
    hero()
    header("h-01.svg", "01 · O que eu faço", "Quatro frentes.", "Um só responsável.")
    header("h-02.svg", "02 · Por que confiar", "Não precisa acreditar.", "Teste.",
           "O site, as demos e o servidor que as entrega são código meu.")
    header("h-03.svg", "03 · Com o que eu construo", "Do banco de dados", "à tela.")
    header("h-04.svg", "04 · Contato", "Tem um projeto?", "Vamos conversar.")
    card_web(); card_fivem(); card_sixm(); card_rpg()
    proofs(); stack(); footer()
    button("btn-discord.svg", "Chamar no Discord", I_DISCORD, True)
    button("btn-site.svg", "Ver o que eu faço", I_GLOBE, False)
    button("btn-mail.svg", "daltonedition156@gmail.com", I_MAIL, False, h=52, size=16, label_alt="E-mail: daltonedition156@gmail.com")
    button("btn-insta.svg", "@dtnedition", I_INSTA, False, h=52, size=16, label_alt="Instagram @dtnedition")
    button("btn-in.svg", "LinkedIn", I_IN, False, h=52, size=16)
