Short answer: PDF doesn’t have a native “strikethrough” text attribute that pdfplumber can read. In practice, strike-through shows up in one of three ways:

1. As a Text Markup annotation of subtype `/StrikeOut` (common in “comments” added with Acrobat)
2. As a thin vector path (a line or very flat rectangle) drawn across the text by the PDF creator
3. Baked into an image (or otherwise flattened), in which case there’s nothing for pdfplumber to detect

pdfplumber can help with (2), and you can heuristically detect strikethrough by correlating words with nearby line/rect objects. It can’t read `/StrikeOut` annotations directly; for (1) you typically pair with a library like `pypdf` to read page annotations.

Here are practical methods you can use with pdfplumber:

#1 Heuristic line/rect overlay detection (works with most generated PDFs)

- Extract words (`page.extract_words()`), plus vector graphics (`page.lines`, `page.rects`).
- For each word box, look for a line/rect whose:

  - Horizontal overlap covers most of the word (e.g., ≥ 60–80% of the word width),
  - Vertical position sits near the word’s midline (roughly halfway between `y0` and `y1` of the word/chars),
  - Thickness is small (e.g., ≤ 5% of the word height).

- Optionally filter by color: use `stroking_color` on lines/rects and `non_stroking_color` on chars to reduce false positives (table borders, underlines).

Sketch:

```python
import pdfplumber

def is_struck_word(word, lines, rects, y_band_frac=(0.35, 0.65), min_cover=0.6, max_thickness_frac=0.08):
    x0, x1, top, bottom = word["x0"], word["x1"], word["top"], word["bottom"]
    h = bottom - top
    # vertical band where a strike line typically sits (middle of the text box)
    y_min = top + y_band_frac[0] * h
    y_max = top + y_band_frac[1] * h
    min_len = (x1 - x0) * min_cover
    max_thickness = h * max_thickness_frac

    def horizontally_covers(obj_x0, obj_x1):
        overlap = max(0, min(x1, obj_x1) - max(x0, obj_x0))
        return overlap >= min_len

    # check lines
    for ln in lines:
        # pdfplumber line has x0,y0,x1,y1 (y increases downward)
        if y_min <= ln["y0"] <= y_max and y_min <= ln["y1"] <= y_max:
            if horizontally_covers(ln["x0"], ln["x1"]):
                # line thickness may be absent; you can approximate using line width if available,
                # or skip this check for lines.
                return True

    # check very flat rects used instead of lines
    for rc in rects:
        thickness = rc["height"]
        y_mid = rc["top"] + thickness / 2
        if thickness <= max_thickness and y_min <= y_mid <= y_max:
            if horizontally_covers(rc["x0"], rc["x1"]):
                return True

    return False

with pdfplumber.open("file.pdf") as pdf:
    for page in pdf.pages:
        words = page.extract_words(use_text_flow=True, keep_blank_chars=False)
        lines = page.lines
        rects = page.rects
        struck = [w for w in words if is_struck_word(w, lines, rects)]
        # `struck` now contains words likely marked as strikethrough
```

Tuning tips:

- Adjust `y_band_frac` based on the PDFs you see. For many engines a strike line sits around 45–55% of the text height; a wider band (e.g., 0.30–0.70) is safer but may add false positives.
- If you work at the character level (`page.chars`) you can be stricter (only accept a line that crosses the majority of the chars in the word and is within each char’s mid band).
- Use color to avoid picking up table rules: require that the line/rect color matches the text color or a small set of expected colors.

#2 Character-level correlation (higher precision)

- Build a word from `page.chars` (group by `word_id` or your own clustering).
- For each char box, test for a line/rect that crosses its center band.
- Mark the word “struck” only if ≥ N% of its chars have a crossing line.
  This reduces false positives from short lines that happen to intersect part of the word.

#3 Annotation detection (not via pdfplumber alone)

- If the source used true “comment” markups, they’ll be `/Annots` of subtype `/StrikeOut`.
- pdfplumber does not (as of today) expose annotations; use `pypdf` (or `PyMuPDF/fitz`) to read them, then map the annotation quadpoints back to text boxes. That path is very reliable when present:

  - Read `/Annots`, filter where `/Subtype == /StrikeOut`.
  - For each strikeout annotation, its `QuadPoints` define the highlighted/struck text region; intersect with your word boxes from pdfplumber to tag those words as struck.

#4 When it won’t work

- If the text was flattened to an image (scanned or rasterized), there are no vector lines or annotations to detect. You’d need OCR plus a visual line detector (e.g., OpenCV) and then remap to recognized text—outside pdfplumber’s scope.

Practical safeguards

- Exclude underlines by requiring the line’s vertical position to be above the text baseline (e.g., above `top + 0.2*h`), not near the bottom.
- Exclude overlines by capping the band below ~80% of height.
- Ignore very thick rects (likely highlights) unless they have tiny thickness.
