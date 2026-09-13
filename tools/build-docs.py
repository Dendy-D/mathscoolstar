#!/usr/bin/env python3
"""
Собирает страницы правовых документов из .docx в docs/*.html.
Текст переносится дословно; скрипт только размечает заголовки, списки и таблицы.

Исходники лежат в docs/files/*.docx — там же, откуда их скачивают с сайта.
Обновился документ — положить новый файл под тем же именем и запустить сборку.

Запуск:  python3 tools/build-docs.py
"""
import html as H, os, re, shutil, zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs')

# Базовый адрес сайта
SITE_URL = 'https://mathscoolstar.ru/'

DOCS = [
    dict(slug='svedeniya',
         src='docs/files/svedeniya.docx',
         h1='Основные сведения об образовательной организации',
         desc='Сведения об ИП Василенко А. В.: реквизиты, деятельность, режим обучения.',
         drop=['Основные сведения об образовательной организации'],
         meta=None, lead=0, toc=False),
    dict(slug='oferta',
         src='docs/files/oferta.docx',
         h1='Публичная оферта',
         sub='Предложение заключить договор оказания образовательных услуг',
         desc='Публичная оферта ИП Василенко А. В. — договор оказания образовательных услуг.',
         drop=['ПУБЛИЧНАЯ ОФЕРТА:',
               'предложение заключить договор оказания образовательных услуг'],
         meta='г. Котельники Московской обл. · В редакции от 24 августа 2026 года',
         meta_src=re.compile(r'^г\.\s*Котельники.*В редакции от'),
         lead=3, toc=True),
    dict(slug='soglasie',
         src='docs/files/soglasie.docx',
         h1='Согласие субъекта на обработку персональных данных',
         desc='Согласие на обработку персональных данных при обращении через формы сайта.',
         drop=['Согласие субъекта на обработку персональных данных',
               'Согласие субъекта на обработку персональных данных'],
         meta=None, lead=0, toc=False),
]

# ── чтение .docx ────────────────────────────────────────────────────────────
def runs(el):
    out = []
    for n in el.iter():
        if n.tag == W + 't':
            out.append(n.text or '')
        elif n.tag == W + 'tab':
            out.append(' ')
        elif n.tag == W + 'br':
            out.append('\n')
    return ''.join(out)

def blocks(path):
    body = ET.fromstring(zipfile.ZipFile(path).read('word/document.xml')).find(W + 'body')
    for child in body:
        if child.tag == W + 'p':
            for line in runs(child).split('\n'):
                line = re.sub(r'[ \t]+', ' ', line).strip()
                if line:
                    yield 'P', line
        elif child.tag == W + 'tbl':
            rows = [[cell_lines(tc) for tc in tr.findall(W + 'tc')]
                    for tr in child.findall(W + 'tr')]
            if rows:
                yield 'TABLE', rows

def cell_lines(tc):
    """Абзацы внутри ячейки — отдельными строками, иначе текст склеивается."""
    out = []
    for p in tc.iter(W + 'p'):
        for line in runs(p).split('\n'):
            line = re.sub(r'\s+', ' ', line).strip()
            if line:
                out.append(line)
    return out

# ── разметка ────────────────────────────────────────────────────────────────
CAPS = re.compile(r'^[А-ЯЁ][А-ЯЁ\s.,\-—:()«»"\']*$')
RULE = re.compile(r'^[_\-—\s]{6,}$')

def is_h2(s):
    m = re.match(r'^(\d+)\.\s+(.+)$', s)
    return bool(m and m.group(2) == m.group(2).upper() and CAPS.match(m.group(2)))

def is_h3(s):
    if s[0].isdigit() or '://' in s:
        return False
    if CAPS.match(s) and 8 <= len(s) <= 90:
        return True
    return s.endswith(':') and len(s) <= 70

def linkify(escaped):
    escaped = re.sub(r'(https?://[^\s<»"]+?)(?=[.,;:)»]?(?:\s|$))',
                     r'<a href="\1" target="_blank" rel="noopener">\1</a>', escaped)
    return re.sub(r'(?<![\w.@-])([\w.+-]+@[\w-]+(?:\.[\w-]+)+)',
                  r'<a href="mailto:\1">\1</a>', escaped)

def esc(s):
    return linkify(H.escape(s))

def slugify(s, i):
    return 'r%d' % i

# ── сборка одной страницы ───────────────────────────────────────────────────
def build(cfg):
    src = cfg['src'] if os.path.isabs(cfg['src']) else os.path.join(ROOT, cfg['src'])
    items = list(blocks(src))
    # выкидываем строки-дубликаты заголовка и строку, ушедшую в подпись
    kept = []
    for kind, val in items:
        if kind == 'P':
            if val in cfg['drop']:
                continue
            if cfg.get('meta_src') and cfg['meta_src'].match(val):
                continue
        kept.append((kind, val))

    lead_n = cfg.get('lead', 0)
    lead = [v for k, v in kept[:lead_n] if k == 'P']
    rest = kept[lead_n:]

    body, toc, sec = [], [], 0
    for kind, val in rest:
        if kind == 'TABLE':
            head, *tail = val
            cell = lambda tag, c: '<%s>%s</%s>' % (
                tag, ''.join('<p>%s</p>' % esc(x) for x in c) or '&nbsp;', tag)
            t = ['<div class="doc-tablewrap"><table class="doc-table">',
                 '<thead><tr>' + ''.join(cell('th', c) for c in head) + '</tr></thead><tbody>']
            for row in tail:
                t.append('<tr>' + ''.join(cell('td', c) for c in row) + '</tr>')
            t.append('</tbody></table></div>')
            body.append('\n'.join(t))
        elif RULE.match(val):
            body.append('<hr class="doc-rule">')
        elif is_h2(val):
            sec += 1
            sid = slugify(val, sec)
            toc.append((sid, re.sub(r'^\d+\.\s*', '', val)))  # номер рисует CSS-счётчик
            body.append('<h2 id="%s">%s</h2>' % (sid, H.escape(val)))
        elif is_h3(val):
            body.append('<h3>%s</h3>' % H.escape(val))
        else:
            body.append('<p>%s</p>' % esc(val))

    # исходный .docx кладём рядом для скачивания
    fname = cfg['slug'] + '.docx'
    dest = os.path.join(OUT, 'files', fname)
    if os.path.abspath(src) != os.path.abspath(dest):
        shutil.copy2(src, dest)
    size_kb = max(1, round(os.path.getsize(dest) / 1024))

    toc_html = ''
    if cfg.get('toc') and len(toc) >= 4:
        toc_html = ('<nav class="doc-toc" aria-label="Содержание">\n<b>Содержание</b>\n<ol>\n'
                    + '\n'.join('<li><a href="#%s">%s</a></li>' % (i, H.escape(t)) for i, t in toc)
                    + '\n</ol>\n</nav>')

    lead_html = ''
    if lead:
        lead_html = ('<aside class="doc-callout">'
                     + ''.join('<p>%s</p>' % esc(l) for l in lead) + '</aside>')

    sub_html = '<p class="doc-sub">%s</p>' % H.escape(cfg['sub']) if cfg.get('sub') else ''
    meta_html = '<p class="doc-meta">%s</p>' % H.escape(cfg['meta']) if cfg.get('meta') else ''

    page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{H.escape(cfg['h1'])} — Василенко А. В.</title>
<meta name="description" content="{H.escape(cfg['desc'])}">
<meta name="theme-color" content="#0F1B2D">
<link rel="canonical" href="{SITE_URL}docs/{cfg['slug']}.html">
<link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../assets/fonts.css">
<link rel="stylesheet" href="../styles.css">
<link rel="stylesheet" href="doc.css">
</head>
<body class="doc-page">

<header class="doc-header">
  <div class="wrap doc-header__inner">
    <a class="brand" href="../index.html">
      <span class="brand__mark" aria-hidden="true">АВ</span>
      <span class="brand__text"><b>Василенко А.&nbsp;В.</b><i>репетитор по математике</i></span>
    </a>
    <a class="doc-back" href="../index.html">← На главную</a>
  </div>
</header>

<main class="wrap doc">
  <p class="eyebrow">Документы</p>
  <h1 class="doc-title">{H.escape(cfg['h1'])}</h1>
  {sub_html}
  {meta_html}
  {lead_html}
  {toc_html}

  <div class="doc-body">
{chr(10).join(body)}
  </div>

  <p class="doc-download">
    <a href="files/{H.escape(fname)}" download>Скачать оригинал документа (DOCX, {size_kb}&nbsp;КБ)</a>
  </p>
</main>

<footer class="doc-footer">
  <div class="wrap">
    <p>ИП Василенко Алевтина Викторовна · ИНН 280108328234 · ОГРНИП 326508100452897</p>
    <p><a href="tel:+79160164559">+7 916 016-45-59</a> · <a href="mailto:infomathege@mail.ru">infomathege@mail.ru</a></p>
    <p class="doc-footer__back"><a href="../index.html">← Вернуться на сайт</a></p>
  </div>
</footer>

</body>
</html>
"""
    with open(os.path.join(OUT, cfg['slug'] + '.html'), 'w', encoding='utf-8') as f:
        f.write(page)
    return cfg['slug'], len(body), sec

if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'files'), exist_ok=True)
    for cfg in DOCS:
        slug, n, sec = build(cfg)
        print(f'  docs/{slug}.html — {n} блоков, {sec} разделов')
