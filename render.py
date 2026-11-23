#!/usr/bin/env python3
"""Nabooq — genera le slide PNG (1080x1350) di un carosello a partire da un file JSON.

Uso:  python3 render.py posts/<cartella>/post.json
Output: posts/<cartella>/slide-01.png, slide-02.png, ...

Tipi di slide: cover, text, list, split, stat, cta. Temi: dark, light, ice.
Nei testi sono ammessi solo: <b>, <br>, <span class="m">seconda riga attenuata</span>, <span class="hl">accento ghiaccio</span>.
Requisiti: Python 3 + Playwright (pip install playwright && playwright install chromium).
"""
import json, sys, pathlib, html
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
CSS = (ROOT / "templates" / "style.css").read_text(encoding="utf-8")
LOGO = (ROOT / "brand" / "nabooq-logo.svg").read_text(encoding="utf-8").replace('width="1812.2641" height="485.7127" ', "").replace("<svg ", '<svg class="logo" ', 1)
MARK = (ROOT / "brand" / "nabooq-mark.svg").read_text(encoding="utf-8").replace("<svg ", '<svg class="mark" ', 1)
CHROME = "/usr/bin/google-chrome"  # sul PC: lasciare None per usare il Chromium di Playwright


def foot(i, n, last):
    arrow = "" if last else '<span class="arrow">→</span>'
    return (f'<div class="foot">{LOGO}'
            f'<div class="page">{i:02d}/{n:02d}{arrow}</div></div>')


def kicker(s):
    return f'<div class="top"><div class="kicker">{s.get("kicker","")}</div>{MARK}</div>'


def fine(s):
    return f'<div class="fineprint muted">{s["fineprint"]}</div>' if s.get("fineprint") else ""


def slide_html(s, i, n):
    t, theme = s["type"], s.get("theme", "light")
    last = i == n
    if t == "cover":
        inner = (f'{kicker(s)}<div class="main"><h1>{s["title"]}</h1>'
                 + (f'<div class="sub muted">{s["sub"]}</div>' if s.get("sub") else "") + "</div>")
    elif t == "text":
        inner = f'{kicker(s)}<h2>{s["title"]}</h2><div class="body">{s["body"]}</div>'
    elif t == "list":
        items = "".join(f'<div class="item"><div class="num">{k+1}</div><div class="t">{x}</div></div>'
                        for k, x in enumerate(s["items"]))
        inner = f'{kicker(s)}<h2>{s["title"]}</h2><div class="items">{items}</div>'
    elif t == "split":
        blocks = "".join(f'<div class="block{" fill" if b.get("fill") else ""}"><div class="lab">{b["label"]}</div>'
                         f'<div class="t">{b["text"]}</div></div>' for b in s["blocks"])
        inner = f'{kicker(s)}<h2>{s["title"]}</h2><div class="blocks">{blocks}</div>'
    elif t == "stat":
        inner = (f'{kicker(s)}<div class="big">{s["big"]}</div><div class="cap">{s["caption"]}</div>'
                 + (f'<div class="note muted">{s["note"]}</div>' if s.get("note") else '<div style="margin-bottom:auto"></div>'))
    elif t == "cta":
        acts = "".join(f'<div class="act"><span>{a["icon"]}</span>{a["text"]}</div>' for a in s.get("actions", []))
        inner = f'{kicker(s)}<div class="main"><h2>{s["title"]}</h2><div class="actions">{acts}</div></div>'
    else:
        raise ValueError(f"tipo di slide sconosciuto: {t}")
    return (f'<!doctype html><html lang="it"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body><div class="slide {t} {theme}">{inner}{fine(s)}{foot(i, n, last)}</div></body></html>')


def render(post_json):
    post_json = pathlib.Path(post_json).resolve()
    data = json.loads(post_json.read_text(encoding="utf-8"))
    out = post_json.parent
    slides = data["slides"]
    n = len(slides)
    files = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME) if CHROME and pathlib.Path(CHROME).exists() else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for i, s in enumerate(slides, 1):
            pg.set_content(slide_html(s, i, n), wait_until="load")
            pg.evaluate("document.fonts.ready")
            # controllo trabocco: il contenuto non deve uscire dalla slide
            over = pg.evaluate("(()=>{const e=document.querySelector('.slide');return e.scrollHeight>e.clientHeight})()")
            if over:
                print(f"ATTENZIONE: slide {i} ha troppo testo, accorciare", file=sys.stderr)
            f = out / f"slide-{i:02d}.png"
            pg.screenshot(path=str(f), clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
            files.append(f)
        b.close()
    (out / "caption.txt").write_text(data["caption"].strip() + "\n", encoding="utf-8")
    print("\n".join(str(f) for f in files))


if __name__ == "__main__":
    render(sys.argv[1])
