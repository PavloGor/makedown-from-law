#!/usr/bin/env python3
# law_to_md.py — Конвертер файлів законів України до Markdown
# Підтримує: .htm/.html, .pdf, .docx
# Вихід: чистий UTF-8 .md файл, 1:1 до тексту (без AI-змін)
# v2 — повний рефактор після аналізу якості виводу

import sys
import re
import unicodedata
from pathlib import Path

# Гарантуємо коректне виведення UTF-8 у Windows консолі
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


# ──────────────────────────────────────────────────────
# Утиліти
# ──────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Unicode NFC + nbsp → space + collapse double spaces (НЕ strip)."""
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\xa0', ' ')
    return re.sub(r'[ \t]{2,}', ' ', text)


def _strip(text: str) -> str:
    return _normalize(text).strip()


def _parse_css_bold(style_text: str) -> set:
    bold = set()
    for m in re.finditer(r'(?:a\.rvts\d+,)?span\.(rvts\d+)\{([^}]+)\}', style_text):
        if 'font-weight:bold' in m.group(2):
            bold.add(m.group(1))
    return bold


def _parse_css_italic(style_text: str) -> set:
    italic = set()
    for m in re.finditer(r'(?:a\.rvts\d+,)?span\.(rvts\d+)\{([^}]+)\}', style_text):
        if 'font-style:italic' in m.group(2):
            italic.add(m.group(1))
    return italic


def _get_cls(tag) -> list:
    c = tag.get('class', [])
    return c.split() if isinstance(c, str) else list(c)


def _fmt(text: str, bold: bool, italic: bool) -> str:
    if not text:
        return ''
    text = text.strip()
    if not text:
        return ''
    if bold and italic:
        return f'***{text}***'
    if bold:
        return f'**{text}**'
    if italic:
        return f'*{text}*'
    return text


# ──────────────────────────────────────────────────────
# Рендер inline span/a → MD рядок  (зберігає пробіли на межах)
# ──────────────────────────────────────────────────────

def _inline(tag, bold_cls: set, italic_cls: set) -> str:
    from bs4 import NavigableString, Tag

    # hidden placeholder (font-size:0px) — просто текст
    if 'font-size:0px' in (tag.get('style') or ''):
        return _normalize(tag.get_text())

    parts = []
    for child in tag.children:
        if isinstance(child, NavigableString):
            t = _normalize(str(child)).replace('\r', '').replace('\n', ' ')
            t = re.sub(r'[ \t]{2,}', ' ', t)
            if t:
                parts.append(t)
        elif isinstance(child, Tag):
            if child.name == 'br':
                parts.append('\n')
            elif child.name in ('span', 'a'):
                parts.append(_inline(child, bold_cls, italic_cls))

    joined = ''.join(parts)
    inner = joined.strip()
    if not inner:
        return ''

    classes = _get_cls(tag)
    is_bold = any(c in bold_cls for c in classes)
    is_italic = any(c in italic_cls for c in classes)
    result = _fmt(inner, is_bold, is_italic)

    # відновлюємо пробіл на межах для коректного злиття слів
    if joined.startswith(' '):
        result = ' ' + result
    if joined.endswith(' '):
        result = result + ' '
    return result


# ──────────────────────────────────────────────────────
# Рендер <p> → рядок MD  (зберігає всі дочірні вузли)
# ──────────────────────────────────────────────────────

def _render_p(p_tag, bold_cls: set, italic_cls: set) -> str:
    from bs4 import NavigableString, Tag

    parts = []
    for child in p_tag.children:
        if isinstance(child, NavigableString):
            t = _normalize(str(child)).replace('\r', '').replace('\n', ' ')
            t = re.sub(r'[ \t]{2,}', ' ', t)
            if t:
                parts.append(t)
        elif isinstance(child, Tag):
            name = child.name
            if name == 'br':
                parts.append('\n')
            elif name in ('span', 'a'):
                parts.append(_inline(child, bold_cls, italic_cls))
            elif name == 'em':
                for sub in child.children:
                    if isinstance(sub, NavigableString):
                        t = _normalize(str(sub)).replace('\r', '').replace('\n', ' ')
                        t = re.sub(r'[ \t]{2,}', ' ', t)
                        if t:
                            parts.append(t)
                    elif isinstance(sub, Tag):
                        if sub.name == 'br':
                            parts.append('\n')
                        elif sub.name in ('span', 'a'):
                            parts.append(_inline(sub, bold_cls, italic_cls))
            elif name == 'img':
                title = child.get('title') or child.get('alt') or ''
                if title:
                    parts.append(f'[{title}]')

    result = ''.join(parts)
    result = re.sub(r'[ \t]{2,}', ' ', result)
    return result.strip()


# ──────────────────────────────────────────────────────
# Конвертація таблиці (справжня, з border>0) → MD
# ──────────────────────────────────────────────────────

def _render_table(table_tag, bold_cls, italic_cls) -> str:
    rows = table_tag.find_all('tr')
    if not rows:
        return ''
    md_rows = []
    for row in rows:
        cells = row.find_all(['td', 'th'])
        row_texts = []
        for cell in cells:
            from bs4 import NavigableString, Tag
            parts = []
            for child in cell.children:
                if isinstance(child, NavigableString):
                    t = _strip(str(child))
                    if t:
                        parts.append(t)
                elif isinstance(child, Tag):
                    if child.name == 'p':
                        parts.append(_render_p(child, bold_cls, italic_cls))
                    elif child.name in ('span', 'a'):
                        parts.append(_inline(child, bold_cls, italic_cls))
                    elif child.name == 'br':
                        parts.append(' ')
                    else:
                        parts.append(_strip(child.get_text(' ')))
            row_texts.append(' '.join(parts).replace('|', '\\|').replace('\n', ' ').strip())
        if any(row_texts):
            md_rows.append(row_texts)
    if not md_rows:
        return ''
    max_cols = max(len(r) for r in md_rows)
    for r in md_rows:
        while len(r) < max_cols:
            r.append('')
    lines = ['| ' + ' | '.join(md_rows[0]) + ' |',
             '|' + '|'.join(['---'] * max_cols) + '|']
    for row in md_rows[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(lines)


# ──────────────────────────────────────────────────────
# Головна функція конвертації HTM → MD
# ──────────────────────────────────────────────────────

# Центровані класи (заголовковий контент)
CENTER_CLS = {'rvps3', 'rvps4', 'rvps6', 'rvps7', 'rvps12', 'rvps17'}
# Класи з відступом злівa (основний текст)
BODY_CLS = {'rvps2', 'rvps8', 'rvps13', 'rvps9', 'rvps18'}


def _plain(text: str) -> str:
    """Видаляє всі MD-маркери форматування."""
    return re.sub(r'\*+', '', text).strip()


def _render_pre_inline(node) -> str:
    """Рендерить вміст inline тегу (em/b/i/a/span/text) всередині pre/p у рядок."""
    from bs4 import NavigableString, Tag
    parts = []
    for child in node.children:
        if isinstance(child, NavigableString):
            t = _normalize(str(child))
            if t:
                parts.append(t)
        elif isinstance(child, Tag):
            name = child.name
            if name == 'br':
                parts.append('\n')
            elif name in ('b', 'strong'):
                inner = _render_pre_inline(child).strip()
                if inner:
                    parts.append(f'**{inner}**')
            elif name in ('em', 'i'):
                inner = _render_pre_inline(child).strip()
                if inner:
                    parts.append(f'*{inner}*')
            elif name == 'a':
                inner = _render_pre_inline(child).strip()
                if inner:
                    parts.append(inner)
            elif name == 'img':
                title = child.get('title') or child.get('alt') or ''
                if title:
                    parts.append(f'[{title}]')
            else:
                parts.append(_render_pre_inline(child))
    return ''.join(parts)


def _render_pre_block(pre_tag) -> str:
    """
    Рендерить <pre> блок у MD-рядок.
    <br> → \n, <b> → **bold**, <em> → *italic*, <a> → plain text.
    Видаляє зайві пробіли між словами (pre зберігає пробіли для форматування).
    """
    from bs4 import NavigableString, Tag
    parts = []
    for child in pre_tag.children:
        if isinstance(child, NavigableString):
            t = _normalize(str(child))
            parts.append(t)
        elif isinstance(child, Tag):
            name = child.name
            if name == 'br':
                parts.append('\n')
            elif name in ('b', 'strong'):
                inner = _render_pre_inline(child).strip()
                if inner:
                    parts.append(f'**{inner}**')
            elif name in ('em', 'i'):
                inner = _render_pre_inline(child).strip()
                if inner:
                    parts.append(f'*{inner}*')
            elif name == 'a':
                inner = _render_pre_inline(child).strip()
                if inner:
                    parts.append(inner)
            elif name == 'img':
                title = child.get('title') or child.get('alt') or ''
                if title:
                    parts.append(f'[{title}]')
            else:
                parts.append(_render_pre_inline(child))

    text = ''.join(parts)
    # Нормалізуємо рядки: collapse пробіли всередині кожного рядка,
    # але зберігаємо розриви рядків
    lines = text.split('\n')
    lines = [re.sub(r'[ \t]{2,}', ' ', ln).strip() for ln in lines]
    # Видаляємо порожні рядки лише з початку і кінця блоку
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
def _render_stamp_node(node) -> str:
    """Рендерить вузол всередині штампу з посиланнями та форматуванням."""
    if not node:
        return ''
    from bs4 import NavigableString, Tag
    parts = []
    for c in node.children:
        if isinstance(c, NavigableString):
            t = unicodedata.normalize('NFC', str(c)).replace('\xa0', ' ').replace('\r', '').replace('\n', ' ')
            t = re.sub(r'[ \t]{2,}', ' ', t)
            if t:
                parts.append(t)
        elif isinstance(c, Tag):
            if c.name == 'br':
                parts.append('\n')
            elif c.name in ('b', 'strong'):
                in_t = _render_stamp_node(c).strip()
                if in_t:
                    parts.append(f'**{in_t}**')
            elif c.name in ('i', 'em'):
                in_t = _render_stamp_node(c).strip()
                if in_t:
                    parts.append(f'*{in_t}*')
            elif c.name == 'a':
                href = c.get('href', '').strip()
                in_t = _render_stamp_node(c).strip()
                if in_t:
                    if href:
                        parts.append(f'[{in_t}]({href})')
                    else:
                        parts.append(in_t)
            elif c.name in ('u', 'font', 'small', 'span'):
                parts.append(_render_stamp_node(c))
            elif c.name != 'img':
                parts.append(_render_stamp_node(c))
    res = ''.join(parts)
    return re.sub(r'[ \t]{2,}', ' ', res).strip()


def _render_stamp(stamp_div) -> list:
    """Рендерить блок метаданих документа (div.stamp) та публікації у список рядків MD."""
    lines = ['---', '', '### Довідка про документ', '']

    tbl = stamp_div.find('table')
    if tbl:
        tds = tbl.find_all('td')
        if len(tds) >= 2:
            # Середня колонка: назва документа, реквізити, редакція, посилання
            mid_cell = tds[1]
            text_mid = _render_stamp_node(mid_cell)
            raw_lines = [ln.strip() for ln in text_mid.split('\n') if ln.strip()]
            # Об'єднуємо розірвану адресу 'Постійна адреса:\nhttps://...'
            merged = []
            i = 0
            while i < len(raw_lines):
                cur = raw_lines[i]
                if cur.rstrip('*_').endswith(':') and i + 1 < len(raw_lines):
                    nxt = raw_lines[i + 1]
                    if nxt.startswith('http') or nxt.startswith('*http') or nxt.startswith('['):
                        cur = f'{cur} {nxt}'
                        i += 1
                merged.append(cur)
                i += 1

            for ln in merged:
                lines.append(f'- {ln}')

        if len(tds) >= 3:
            # Права колонка: статус чинності, дата бази
            right_cell = tds[2]
            text_r = _render_stamp_node(right_cell)
            r_parts = [p.strip() for p in text_r.split('\n') if p.strip()]
            if r_parts:
                lines.append(f'- **Стан:** ' + ', '.join(r_parts))

    # Публікації документа
    hdr = stamp_div.find(['h1', 'h2', 'h3', 'h4'])
    if hdr:
        lines.append('')
        h_text = _render_stamp_node(hdr).strip()
        lines.append(f'### {h_text}')
        lines.append('')

    ul = stamp_div.find(['ul', 'ol'])
    if ul:
        for li in ul.find_all('li'):
            li_t = _render_stamp_node(li).strip()
            if li_t:
                lines.append(f'- {li_t}')

    return lines


def convert_htm_to_md(input_path: Path) -> str:
    from bs4 import BeautifulSoup, NavigableString, Tag

    raw = input_path.read_bytes()
    try:
        html = raw.decode('utf-8')
    except UnicodeDecodeError:
        html = raw.decode('windows-1251', errors='replace')

    soup = BeautifulSoup(html, 'lxml')

    # ── CSS → множини bold/italic класів ──
    all_style = ' '.join(t.get_text(' ') for t in soup.find_all('style'))
    bold_cls = _parse_css_bold(all_style)
    italic_cls = _parse_css_italic(all_style)

    # ── Основний блок контенту ──
    article = soup.find('div', id='article') or soup.find('body') or soup

    out = []   # фінальні рядки виводу

    def add(line: str = ''):
        out.append(line)

    def add_blank():
        if out and out[-1] != '':
            out.append('')

    def add_bq(text: str):
        """Додає рядок як blockquote, підтримує внутрішні \n."""
        lines = text.split('\n')
        for ln in lines:
            out.append('> ' + ln if ln.strip() else '>')

    def process(node, in_em: bool = False):
        if isinstance(node, NavigableString):
            return
        tag_name = getattr(node, 'name', None)
        if not tag_name:
            return
        if tag_name in ('style', 'script', 'head'):
            return

        # ── img ──
        if tag_name == 'img':
            title_attr = node.get('title') or node.get('alt') or ''
            if title_attr:
                add_blank()
                add(f'[{title_attr}]')
                add_blank()
            return

        # ── em — всі дочірні <p>/<pre> — blockquote ──
        if tag_name == 'em':
            # Якщо em — inline (всередині pre або p) — рендеримо як курсив
            parent_name = getattr(node.parent, 'name', '')
            if parent_name in ('pre', 'p', 'td', 'b', 'span'):
                text = _render_pre_inline(node)
                if text:
                    add_blank()
                    add_bq(f'*{text}*' if not text.startswith('*') else text)
            else:
                for child in node.children:
                    if isinstance(child, Tag):
                        process(child, in_em=True)
            return

        # ── pre — блок preformatted (старий стиль rada.gov.ua) ──
        if tag_name == 'pre':
            text = _render_pre_block(node)
            if not text:
                return
            # Перевіряємо em всередині — якщо є, blockquote
            has_em = bool(node.find('em'))
            # bold всередині → центральний заголовок або bold параграф
            has_b = bool(node.find('b'))
            if has_em and not has_b:
                add_blank()
                for line in text.split('\n'):
                    line = line.strip()
                    if line:
                        fmted = f'*{line}*' if not (line.startswith('*') and line.endswith('*')) else line
                        out.append('> ' + fmted)
                return
            # Звичайний pre блок
            add_blank()
            for line in text.split('\n'):
                stripped = line.strip()
                if stripped:
                    add(stripped)
            return

        # ── h1-h6 ──
        if re.match(r'h[1-6]$', tag_name):
            level = int(tag_name[1])
            text = _strip(node.get_text(' '))
            if text:
                add_blank()
                add('#' * level + ' ' + text)
                add_blank()
            return

        # ── ul/ol ──
        if tag_name in ('ul', 'ol'):
            add_blank()
            for li in node.find_all('li', recursive=False):
                text = _strip(li.get_text(' '))
                if text:
                    add(f'- {text}')
            add_blank()
            return

        # ── small, font — ігноруємо (метадані штампу) ──
        if tag_name in ('small', 'font'):
            return

        # ── table ──
        if tag_name == 'table':
            border = (node.get('border') or '').strip()
            if border in ('', '0') or not border:
                # layout table — обходимо <p>/<pre> всередині
                for child in node.find_all(['p', 'pre'], recursive=True):
                    process(child, in_em=in_em)
            else:
                tbl = _render_table(node, bold_cls, italic_cls)
                if tbl:
                    add_blank()
                    add(tbl)
                    add_blank()
            return

        # ── p ──
        if tag_name == 'p':
            classes = set(_get_cls(node))
            raw_text = _render_p(node, bold_cls, italic_cls)
            if not raw_text:
                return
            plain = _plain(raw_text)
            is_center = bool(classes & CENTER_CLS)
            has_bold_span = bool(node.find(
                lambda t: t.name in ('span', 'a') and
                any(c in bold_cls for c in _get_cls(t))
            ))

            # ── Заголовок «ЗАКОН УКРАЇНИ» ──
            if is_center and re.match(r'ЗАКОН УКРАЇНИ', plain, re.IGNORECASE):
                add_blank()
                add('# ЗАКОН УКРАЇНИ')
                add_blank()
                return

            # ── Назва закону (центр, bold, великий шрифт) ──
            if is_center and has_bold_span and not in_em:
                clean = re.sub(r'\s+', ' ', plain.replace('\n', ' ')).strip()
                # Розділ / Глава / Книга / Частина → ##
                if re.match(r'(?:Розділ|Глава|Книга|Частина|Підрозділ)\s+[IVXLCDM\d]+', clean, re.IGNORECASE):
                    add_blank()
                    # Заголовок і назва можуть бути розділені \n (<br>)
                    parts = re.sub(r'\*+', '', raw_text).split('\n')
                    parts = [p.strip() for p in parts if p.strip()]
                    if len(parts) >= 2:
                        add(f'## {parts[0]}')
                        add_blank()
                        add(f'### {parts[1]}')
                    else:
                        add(f'## {clean}')
                    add_blank()
                    return
                # Назва закону (перший центральний bold рядок після ЗАКОН УКРАЇНИ)
                add_blank()
                add(f'# {clean}')
                add_blank()
                return

            # ── Центр, italic (Відомості ВВР…) — курсивний рядок ──
            if is_center and in_em:
                clean = re.sub(r'\s+', ' ', plain.replace('\n', ' ')).strip()
                add_blank()
                add(f'*({clean})*' if not clean.startswith('(') else f'*{clean}*')
                add_blank()
                return

            # ── Стаття N. … — заголовок → ### ──
            bare = _plain(raw_text)
            if re.match(r'Стаття\s+\d', bare):
                clean = re.sub(r'\s+', ' ', bare).strip()
                add_blank()
                add(f'### {clean}')
                add_blank()
                return

            # ── em / in_em → blockquote ──
            if in_em:
                if raw_text:
                    # Split on \n (from <br>) — each sub-line gets its own "> " prefix without empty lines
                    sub_lines = [s.strip() for s in raw_text.split('\n') if s.strip()]
                    add_blank()
                    for sl in sub_lines:
                        fmted = f'*{sl}*' if not (sl.startswith('*') and sl.endswith('*')) else sl
                        out.append('> ' + fmted)
                return

            # ── Звичайний текст (rvps2 тощо) ──
            # Розбиваємо за \n (з HTML <br>) — кожен підпараграф = окремий рядок
            sub_parts = raw_text.split('\n')
            add_blank()
            for sp in sub_parts:
                sp = sp.strip()
                if sp:
                    add(sp)
            return

        # ── hr ──
        if tag_name == 'hr':
            add_blank()
            add('---')
            add_blank()
            return

        # ── div, body тощо — просто обходимо дочірні ──
        if tag_name in ('div', 'body', 'html'):
            # Пропускаємо блок метаданих (.stamp) — це реквізити штампу, не зміст
            classes = set(_get_cls(node))
            if 'stamp' in classes:
                return
            for child in node.children:
                if isinstance(child, Tag):
                    process(child, in_em=in_em)
            return

        # ── решта — обходимо дочірні ──
        for child in node.children:
            if isinstance(child, Tag):
                process(child, in_em=in_em)

    process(article)

    # ── Блок stamp (Довідка про документ та публікації) ──
    stamp = soup.find('div', class_='stamp') or soup.find(
        lambda t: getattr(t, 'name', None) == 'div' and 'stamp' in _get_cls(t)
    )
    if stamp:
        add_blank()
        for sl in _render_stamp(stamp):
            add(sl)
        add_blank()

    # ── Постобробка ──
    md = '\n'.join(out)
    # Не більше 2 порожніх рядки підряд
    md = re.sub(r'\n{3,}', '\n\n', md)
    # Trailing spaces
    md = '\n'.join(line.rstrip() for line in md.splitlines())
    return md.strip() + '\n'


# ──────────────────────────────────────────────────────
# PDF / DOCX → MD (через markitdown)
# ──────────────────────────────────────────────────────

def convert_pdf_to_md(input_path: Path) -> str:
    from markitdown import MarkItDown
    return MarkItDown().convert(str(input_path)).text_content


def convert_docx_to_md(input_path: Path) -> str:
    from markitdown import MarkItDown
    return MarkItDown().convert(str(input_path)).text_content


# ──────────────────────────────────────────────────────
# Публічний API
# ──────────────────────────────────────────────────────

SUPPORTED = {
    '.htm': convert_htm_to_md,
    '.html': convert_htm_to_md,
    '.pdf': convert_pdf_to_md,
    '.docx': convert_docx_to_md,
}


def convert_file(input_path: Path, output_dir=None) -> Path:
    input_path = Path(input_path).resolve()
    suffix = input_path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f'Непідтримуваний тип: {suffix}. Підтримується: {list(SUPPORTED)}')
    print(f'  Конвертую: {input_path.name}')
    md_text = SUPPORTED[suffix](input_path)
    out_dir = Path(output_dir) if output_dir else input_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (input_path.stem + '.md')
    out_path.write_text(md_text, encoding='utf-8')
    print(f'  ✓ Збережено: {out_path}')
    return out_path


def main():
    import argparse, glob
    parser = argparse.ArgumentParser(
        description='Конвертер файлів законів України у Markdown (UTF-8)',
        epilog='Приклад: py law_to_md.py Examples/ --output Output/'
    )
    parser.add_argument('inputs', nargs='+', help='Файли або теки')
    parser.add_argument('--output', '-o', default=None, help='Тека для .md файлів')
    parser.add_argument('--no-dedup', action='store_true',
                        help='Не видаляти дублікати за stem (конвертувати всі формати)')
    args = parser.parse_args()

    FORMAT_PRIORITY = ['.htm', '.html', '.docx', '.pdf']

    raw_files = []
    for pattern in args.inputs:
        p = Path(pattern)
        if p.is_dir():
            for ext in SUPPORTED:
                raw_files.extend(p.glob(f'*{ext}'))
        else:
            matched = glob.glob(pattern)
            if matched:
                raw_files.extend(Path(f) for f in matched)
            elif p.exists():
                raw_files.append(p)
            else:
                print(f'  ⚠ Не знайдено: {pattern}', file=sys.stderr)

    if not raw_files:
        print('Помилка: файли не знайдено.', file=sys.stderr)
        sys.exit(1)

    if not args.no_dedup:
        by_stem: dict[str, Path] = {}
        for f in raw_files:
            stem = f.stem
            ext = f.suffix.lower()
            if stem not in by_stem:
                by_stem[stem] = f
            else:
                existing_ext = by_stem[stem].suffix.lower()
                existing_pri = FORMAT_PRIORITY.index(existing_ext) if existing_ext in FORMAT_PRIORITY else 99
                new_pri = FORMAT_PRIORITY.index(ext) if ext in FORMAT_PRIORITY else 99
                if new_pri < existing_pri:
                    by_stem[stem] = f
        all_files = list(by_stem.values())
        skipped = len(raw_files) - len(all_files)
        if skipped:
            print(f'  ℹ Дедуплікація: обрано {len(all_files)} унікальних законів ({skipped} дублікатів інших форматів пропущено)')
    else:
        all_files = raw_files

    print(f'\nЗнайдено {len(all_files)} файл(ів) для конвертації\n')
    ok = errors = 0
    for f in sorted(all_files):
        try:
            convert_file(f, args.output)
            ok += 1
        except Exception as e:
            print(f'  ✗ Помилка [{f.name}]: {e}', file=sys.stderr)
            errors += 1

    print(f'\nГотово: {ok} успішно, {errors} помилок.')


if __name__ == '__main__':
    main()

