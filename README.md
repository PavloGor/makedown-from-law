# Law-to-Markdown (Ukrainian Legislation Converter for AI & LLMs)

> **High-fidelity, zero-loss converter for Ukrainian legislation documents (`zakon.rada.gov.ua`) from HTML/HTM, DOCX, and PDF to clean, LLM-optimized UTF-8 Markdown.**
>
> 🇺🇦 **Високоточний конвертер нормативно-правових актів та законів України (`zakon.rada.gov.ua`) з форматів HTML/HTM, DOCX та PDF у чистий Markdown (UTF-8), оптимізований для систем штучного інтелекту, LLM (GPT-4o, Claude, Gemini) та RAG-пайплайнів із 100% точним збереженням юридичного тексту без змін.**

---

## Table of Contents
- [Overview](#overview)
- [Why Markdown for AI & LLMs?](#why-markdown-for-ai--llms)
- [Token & File Size Comparison Benchmark](#token--file-size-comparison-benchmark)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Installation & Requirements](#installation--requirements)
- [Usage](#usage)
  - [1. Windows Interactive Launcher (`convert.cmd`)](#1-windows-interactive-launcher-convertcmd)
  - [2. Command Line Interface (CLI)](#2-command-line-interface-cli)
  - [3. Python API](#3-python-api)
- [Document Structure Mapping](#document-structure-mapping)
- [License](#license)

---

## Overview

Official Ukrainian legislative documents published on [zakon.rada.gov.ua](https://zakon.rada.gov.ua) contain rich metadata, complex CSS styling (`rvts*` / `rvps*` classes), editorial amendment brackets (`{Із змінами...}`), nested section hierarchies, and layout tables.

When feeding raw HTML files into Large Language Models (LLMs) like GPT-4o, Claude 3.5, Gemini 1.5/2.0, or open-source models:
- **Excessive token consumption**: 30% to 50%+ of the context window is wasted on CSS classes, inline font tags, and base64 images.
- **Degraded retrieval & reasoning**: Tag clutter confuses chunking algorithms in RAG pipelines and distracts LLM attention mechanisms.
- **Risk of text corruption**: Generic converters often strip whitespace between adjacent inline tags (e.g. `регулюютьсяКонституцією`) or break article numbering.

**Law-to-Markdown** solves this by providing a specialized, CSS-aware, 1:1 text-preserving parser tailored specifically for Ukrainian laws, codes, and normative acts.

> 🇺🇦 **Офіційні законодавчі документи України на порталі [zakon.rada.gov.ua](https://zakon.rada.gov.ua) містять розгалужені метадані, складні CSS-стилі (класи `rvts*` / `rvps*`), редакційні примітки про внесені зміни (`{Із змінами...}`), багаторівневу ієрархію розділів та таблиці розмітки.**
>
> **При передачі вихідних HTML-файлів у великі мовні моделі (LLM), такі як GPT-4o, Claude 3.5, Gemini 1.5/2.0 чи локальні моделі:**
> - **Надмірне споживання токенів**: від 30% до 50%+ контекстного вікна витрачається даремно на службові CSS-класи, теги стилів та base64-зображення.
> - **Погіршення пошуку та логічного аналізу**: тегове сміття заважає алгоритмам розбиття на чанки в RAG-пайплайнах та розсіює увагу нейромережі.
> - **Ризик пошкодження тексту**: стандартні конвертери часто зливають слова на стиках тегів (наприклад, `регулюютьсяКонституцією`) або спотворюють нумерацію статей.
>
> **Law-to-Markdown вирішує ці проблеми завдяки спеціалізованому CSS-аналізатору, який точно зберігає оригінальний юридичний текст 1:1 без втрат і оптимізує його структуру під зручний для AI формат Markdown.**

---

## Why Markdown for AI & LLMs?

### 1. Massive Token Savings
Every HTML tag (`<p class="rvps2"><span class="rvts9">...</span></p>`) contributes extra tokens to the LLM prompt. By transforming visual hierarchy into concise Markdown (`#`, `##`, `###`, `> *...*`), the token count is reduced by **33% to 45%** with **zero loss of legal content**.

### 2. Cleaner RAG & Chunking
Vector databases and text splitters work substantially better on Markdown headings (`### Стаття 1. Публічна інформація`) than on arbitrary `<div>` containers. Headings create natural semantic boundaries for chunking.

### 3. Clear Editorial & Amendment Separation
Amendments and constitutional court notes are automatically grouped into standard Markdown blockquotes (`> *{...}*`), enabling LLMs to clearly distinguish between active legal norms and historical editorial annotations.

---

## 📊 Token & File Size Comparison Benchmark

Comparison of original official HTML downloads (`.htm`) vs. converted Markdown (`.md`):

```text
┌────────────────────────────────────┬──────────────┬────────────┬─────────────┬───────────────┬────────────────────────────┐
│ Document                           │ Format       │ File Size  │ Reduction   │ Est. LLM      │ Tokens Saved               │
│                                    │              │            │             │ Tokens        │                            │
├────────────────────────────────────┼──────────────┼────────────┼─────────────┼───────────────┼────────────────────────────┤
│ Labor Code of Ukraine              │ HTML         │ 907.0 KB   │             │ 228,979       │ 🔥 76,242 tokens           │
│ (Кодекс законів про працю          │ (.htm)       │            │   -29.1%    │               │    saved (-33.3%)          │
│ України, № 322-VIII)               │ Markdown     │ 642.8 KB   │             │ 152,737       │                            │
│                                    │ (.md)        │            │             │               │                            │
├────────────────────────────────────┼──────────────┼────────────┼─────────────┼───────────────┼────────────────────────────┤
│ Law on Vacations                   │ HTML         │ 173.9 KB   │             │ 44,638        │ 🔥 18,867 tokens           │
│ (Закон «Про відпустки»,            │ (.htm)       │            │   -37.7%    │               │    saved (-42.3%)          │
│ № 504/96-ВР)                       │ Markdown     │ 108.3 KB   │             │ 25,771        │                            │
│                                    │ (.md)        │            │             │               │                            │
├────────────────────────────────────┼──────────────┼────────────┼─────────────┼───────────────┼────────────────────────────┤
│ Law on Access to Public            │ HTML         │ 121.4 KB   │             │ 31,104        │ 🔥 13,223 tokens           │
│ Information                        │ (.htm)       │            │   -37.8%    │               │    saved (-42.5%)          │
│ (Закон «Про доступ до публічної    │ Markdown     │ 75.5 KB    │             │ 17,881        │                            │
│ інформації», № 2939-VI)            │ (.md)        │            │             │               │                            │
├────────────────────────────────────┼──────────────┼────────────┼─────────────┼───────────────┼────────────────────────────┤
│ Enactment Resolution               │ HTML         │ 9.7 KB     │             │ 2,554         │ 🔥 2,359 tokens            │
│ (Постанова про введення в дію,     │ (.htm)       │            │   -91.8%    │               │    saved (-92.4%)          │
│ № 505/96-ВР)                       │ Markdown     │ 0.8 KB     │             │ 195           │                            │
│                                    │ (.md)        │            │             │               │                            │
└────────────────────────────────────┴──────────────┴────────────┴─────────────┴───────────────┴────────────────────────────┘
```

> 💡 *In a full legal RAG pipeline processing hundreds of statutes, this translates to hundreds of thousands of dollars saved on LLM API calls and substantially faster response times.*

---

## ✨ Key Features

- **🎯 Exact 1:1 Legal Text Fidelity**: Zero generative rewriting, paraphrasing, or hallucinations. Every legal clause, punctuation mark, and reference is preserved exactly as published.
- **🎨 Dynamic CSS Rule Analyzer**: Parses embedded `<style>` sheets at runtime to accurately map `rvts*` font weights and `rvps*` alignments to `#` (H1), `##` (H2), and `###` (H3) Markdown headers.
- **🏛️ Structural Heading Intelligence**: Detects Codes (`Кодекс...`), Laws (`ЗАКОН УКРАЇНИ`), Sections (`Розділ I`), Chapters (`Глава I`, `ГЛАВА III-Б`), and Articles (`Стаття 1.`, `Стаття 2-1.`, `Стаття 4-2.`).
- **📑 Amendment & Gazette Formatting**:
  - Official Gazette references `(Відомості Верховної Ради...)` rendered as clean italic notes.
  - Multi-line amendment blocks formatted as clean, compact blockquotes (`> *...*`) without blank lines.
- **🗂️ Document Metadata & Publication Stamp**: Parses footer stamp (`<div class="stamp">`) into structured metadata (Revision, Legal Ground, Permanent URL, Status, Publication sources).
- **🔄 Smart Format Prioritization & Deduplication**: When a folder contains `.htm`, `.docx`, and `.pdf` versions of the same law, the script automatically selects the highest quality source (`.htm` > `.html` > `.docx` > `.pdf`) without overwriting.
- **💻 Interactive Windows Launcher (`convert.cmd`)**: Numbered interactive menu [1-6], drag-and-drop file support, and automatic UTF-8 console configuration (`chcp 65001`).

---

## Project Structure

```
makedown-from-law/
├── law_to_md.py         # Main Python conversion engine
├── convert.cmd          # Windows interactive batch menu & drag-and-drop runner
├── input/               # Drop folder for bulk batch conversion
│   ├── Про відпустки ... .htm
│   └── Про доступ до публічної інформації ... .htm
├── Output/              # Destination folder for converted .md files
└── README.md            # Documentation and benchmarks
```

---

## Installation & Requirements

### Requirements
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- **Windows / Linux / macOS**

### Dependencies
Install the required packages:

```bash
pip install beautifulsoup4 lxml markitdown
```

---

## 🚀 Usage

### 1. Windows Interactive Launcher (`convert.cmd`)
Simply **double-click** `convert.cmd` or run it from Command Prompt / PowerShell:

```cmd
convert.cmd
```

An interactive menu will appear:
```text
================================================================
          КОНВЕРТЕР ЗАКОНІВ УКРАЇНИ В MARKDOWN (UTF-8)
================================================================

 [1] Пакетна конвертація з папки "input" (всі файли -> Output)
 [2] Конвертувати окремий файл (ввести шлях або перетягнути сюди)
 [3] Конвертувати тільки .htm / .html з папки "input"
 [4] Вказати власні папки (Вхідна тека -> Вихідна тека)
 [5] Відкрити папку з результатами (Output)
 [0] Вихід

================================================================
Оберіть варіант [0-5] і натисніть Enter:
```

> 💡 **Drag & Drop Tip**: You can drag and drop any `.htm`, `.html`, `.docx`, or `.pdf` file directly onto the `convert.cmd` file in Windows Explorer to convert it instantly!

---

### 2. Command Line Interface (CLI)

#### Batch convert a folder:
```bash
py law_to_md.py input/ --output Output/
```

#### Convert specific files:
```bash
py law_to_md.py "Examples/Про відпустки - Закон № 504_96-ВР від 15.11.1996 - d11440-20251012.htm" --output Output/
```

#### Convert all formats without deduplication:
```bash
py law_to_md.py Examples/ --output Output/ --no-dedup
```

---

### 3. Python API

You can easily integrate `law_to_md` into your Python RAG or NLP pipeline:

```python
from pathlib import Path
from law_to_md import convert_htm_to_md, convert_file

# Convert HTML string directly
htm_path = Path("path/to/law.htm")
md_text = convert_htm_to_md(htm_path)

# Or convert and save directly
out_md_path = convert_file("path/to/law.htm", output_dir="Output")
print(f"Saved to: {out_md_path}")
```

---

## Document Structure Mapping

| HTML Element (zakon.rada.gov.ua) | Output Markdown | Description |
| :--- | :--- | :--- |
| `<img title="Герб України">` | `[Герб України]` | Coat of arms text indicator |
| `<p class="rvps17"><span class="rvts78">ЗАКОН УКРАЇНИ</span></p>` | `# ЗАКОН УКРАЇНИ` | Document category (H1) |
| `<p class="rvps6"><span class="rvts23">Про відпустки</span></p>` | `# Про відпустки` | Main Law / Code Title (H1) |
| `<em><p class="rvps7">(Відомості ВВР...)</p></em>` | `*(Відомості ВВР...)*` | Official gazette publication reference |
| `<em><p class="rvps18">{Із змінами...}</p></em>` | `> *{Із змінами...}*` | Editorial amendment notes in blockquote |
| `<p class="rvps7"><span class="rvts15">Розділ I</span><br><span>ЗАГАЛЬНІ...</span></p>` | `## Розділ I`<br>`### ЗАГАЛЬНІ ПОЛОЖЕННЯ` | Major section division & title |
| `<p class="rvps7"><span class="rvts15">Глава I</span><br><span>...</span></p>` | `## Глава I`<br>`### ...` | Code chapter division & title |
| `<p class="rvps2"><span class="rvts9">Стаття 1.</span> Title</p>` | `### Стаття 1. Title` | Article heading (H3) |
| `<div class="stamp">...</div>` | `---`<br>`### Довідка про документ`<br>`- Редакція...`<br>`- Постійна адреса...`<br>`### Публікації документа`<br>`- ...` | Official document stamp & publications metadata |

---

## Output Sample Preview

```markdown
[Герб України]

# ЗАКОН УКРАЇНИ

# Про доступ до публічної інформації

*(Відомості Верховної Ради України (ВВР), 2011, № 32, ст. 314)*

> *{Із змінами, внесеними згідно із Законами*
> *№ 4652-VI від 13.04.2012, ВВР, 2013, № 21, ст.208*
> *№ 4711-VI від 17.05.2012, ВВР, 2013, № 14, ст.89*
> ...
> *№ 4321-IX від 25.03.2025}*

Цей Закон визначає порядок здійснення та забезпечення права кожного на доступ до інформації...

## Розділ I

### ЗАГАЛЬНІ ПОЛОЖЕННЯ

### Стаття 1. Публічна інформація

1. Публічна інформація - це відображена та задокументована будь-якими засобами...

---

### Довідка про документ

- Про доступ до публічної інформації
- Закон України від 13.01.2011 № 2939-VI
- **Редакція** від **08.08.2025**, підстава — [4321-IX](https://zakon.rada.gov.ua/laws/show/4321-20)
- *Постійна адреса: https://zakon.rada.gov.ua/go/2939-17*
- **Стан:** **Законодавство України**, станом на 20.08.2026, чинний

### Публікації документа

- **Голос України** від 09.02.2011 — № 24
- **Урядовий кур'єр** від 15.02.2011 — № 28
- **Відомості Верховної Ради України** від 12.08.2011 — 2011 р., № 32, стор. 1491, стаття 314
```

---

## Creator & License

- **Creator**: **Paul Gorinetsky**
- **License**: [MIT License](LICENSE) — Open-source and free for commercial and non-commercial use.