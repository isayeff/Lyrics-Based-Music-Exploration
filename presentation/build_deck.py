"""Generates the mock-presentation deck as a .pptx.

Re-runnable: edit the SLIDES data below and re-run to regenerate.
    python build_deck.py
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# palette matched to the app
BG = RGBColor(0x0A, 0x0A, 0x0B)
SURFACE = RGBColor(0x14, 0x14, 0x16)
BORDER = RGBColor(0x26, 0x26, 0x2A)
TEXT = RGBColor(0xF5, 0xF5, 0xF5)
MUTED = RGBColor(0x8A, 0x8A, 0x90)
ACCENT = RGBColor(0xE8, 0x00, 0x03)
BLUE = RGBColor(0x7D, 0xD3, 0xFC)
AMBER = RGBColor(0xFC, 0xD3, 0x4D)
GREEN = RGBColor(0x5B, 0xB9, 0x8C)

W, H = Inches(13.333), Inches(7.5)
FONT = "Segoe UI"

prs = Presentation()
prs.slide_width, prs.slide_height = W, H


def blank():
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(1, 0, 0, W, H)  # rectangle
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    bg.line.fill.background()
    bg.shadow.inherit = False
    return s


def textbox(slide, x, y, w, h, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].alignment = align
    return tf


def para(tf, text, size=18, color=TEXT, bold=False, space_before=0, space_after=6,
         align=PP_ALIGN.LEFT, first=False, italic=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = FONT
    return p


def accent_rule(slide, x, y, h=Inches(0.42)):
    bar = slide.shapes.add_shape(1, x, y, Inches(0.06), h)
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    bar.shadow.inherit = False
    return bar


def title_slide(slide, title, kicker=None, sub=None):
    """Section/title heading with accent rule."""
    accent_rule(slide, Inches(0.85), Inches(0.62))
    tf = textbox(slide, Inches(1.05), Inches(0.5), Inches(11.4), Inches(1.0))
    if kicker:
        para(tf, kicker.upper(), size=12, color=ACCENT, bold=True, space_after=2, first=True)
        para(tf, title, size=32, bold=True, space_after=0)
    else:
        para(tf, title, size=32, bold=True, space_after=0, first=True)
    if sub:
        stf = textbox(slide, Inches(1.05), Inches(1.42), Inches(11.4), Inches(0.5))
        para(stf, sub, size=15, color=MUTED, first=True)


def card(slide, x, y, w, h, fill=SURFACE):
    box = slide.shapes.add_shape(5, x, y, w, h)  # rounded rectangle
    box.fill.solid()
    box.fill.fore_color.rgb = fill
    box.line.color.rgb = BORDER
    box.line.width = Pt(1)
    box.shadow.inherit = False
    box.adjustments[0] = 0.06
    return box


def placeholder(slide, x, y, w, h, label):
    box = slide.shapes.add_shape(5, x, y, w, h)
    box.fill.solid()
    box.fill.fore_color.rgb = SURFACE
    box.line.color.rgb = ACCENT
    box.line.width = Pt(1.5)
    box.line.dash_style = 2  # dashed
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = ACCENT
    r.font.name = FONT
    return box


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def bullets(slide, items, x=Inches(1.05), y=Inches(2.15), w=Inches(11.4), size=18, gap=14):
    tf = textbox(slide, x, y, w, Inches(4.6))
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            label, body = item
            p = para(tf, label, size=size, bold=True, color=TEXT,
                     space_before=0 if i == 0 else gap, space_after=2, first=(i == 0))
            para(tf, body, size=size - 3, color=MUTED, space_after=0)
        else:
            para(tf, item, size=size, color=TEXT,
                 space_before=0 if i == 0 else gap, space_after=0, first=(i == 0))
    return tf


def table(slide, data, x, y, w, h, highlight_rows=(), col_widths=None):
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(rows, cols, x, y, w, h)
    tbl = shape.table
    if col_widths:
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = cw
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = str(val)
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = RGBColor(0x1C, 0x1C, 0x1F)
            elif r in highlight_rows:
                cell.fill.fore_color.rgb = RGBColor(0x24, 0x10, 0x12)
            else:
                cell.fill.fore_color.rgb = SURFACE
            cell.margin_left, cell.margin_right = Inches(0.1), Inches(0.08)
            cell.margin_top, cell.margin_bottom = Inches(0.05), Inches(0.05)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            for run in p.runs:
                run.font.size = Pt(13)
                run.font.name = FONT
                run.font.bold = (r == 0) or (r in highlight_rows)
                if r == 0:
                    run.font.color.rgb = MUTED
                elif r in highlight_rows:
                    run.font.color.rgb = RGBColor(0xFF, 0x8A, 0x8C)
                else:
                    run.font.color.rgb = TEXT
    return tbl


def footer(slide, n):
    tf = textbox(slide, Inches(12.1), Inches(6.92), Inches(0.9), Inches(0.35),
                 align=PP_ALIGN.RIGHT)
    para(tf, str(n), size=11, color=RGBColor(0x50, 0x50, 0x56), first=True)


# ---------------------------------------------------------------- slides ----

# 1 — title
s = blank()
bar = s.shapes.add_shape(1, 0, Inches(3.02), W, Inches(0.035))
bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()
bar.shadow.inherit = False
tf = textbox(s, Inches(1.1), Inches(2.0), Inches(11.2), Inches(1.0))
para(tf, "NoLyrics.find", size=54, bold=True, first=True)
tf2 = textbox(s, Inches(1.1), Inches(3.25), Inches(11.2), Inches(1.4))
para(tf2, "Finding songs from how you describe them — not what you can name",
     size=21, color=MUTED, first=True)
para(tf2, "Free-text music retrieval over 84,103 songs using sentence embeddings",
     size=15, color=RGBColor(0x60, 0x60, 0x66), space_before=10)
tf3 = textbox(s, Inches(1.1), Inches(5.9), Inches(11.2), Inches(0.9))
para(tf3, "Elvin Isayev", size=16, bold=True, first=True)
para(tf3, "MSc Dissertation · University of Sheffield · Supervisor: Varvara Papazoglou",
     size=13, color=MUTED, space_before=2)
notes(s, "15 minutes: ~11 on slides, ~4 on the live demo. Open with the problem, "
         "not the technology.")

# 2 — the problem
s = blank()
title_slide(s, "You know the song. You just can't name it.", kicker="The problem")
tf = textbox(s, Inches(1.05), Inches(2.1), Inches(6.4), Inches(3.6))
para(tf, "“That song about someone driving away from a town\nthey know they'll never come back to.”",
     size=26, italic=True, color=TEXT, first=True)
para(tf, "No title. No artist. No lyrics you can quote.", size=17, color=MUTED, space_before=18)
para(tf, "Every music search box today assumes you already know the answer. "
         "Type that sentence into Spotify and you get nothing useful.",
     size=16, color=MUTED, space_before=14)
c = card(s, Inches(7.9), Inches(2.1), Inches(4.4), Inches(3.2))
ctf = c.text_frame; ctf.word_wrap = True
ctf.margin_left = ctf.margin_right = Inches(0.3)
ctf.margin_top = Inches(0.28)
para(ctf, "What search boxes expect", size=13, bold=True, color=MUTED, first=True)
para(ctf, "“bohemian rhapsody”", size=17, color=TEXT, space_before=8)
para(ctf, "“queen”", size=17, color=TEXT, space_before=4)
para(ctf, "What people actually have", size=13, bold=True, color=ACCENT, space_before=22)
para(ctf, "a feeling, a scene, a half-memory of what it was about",
     size=17, color=TEXT, space_before=8)
footer(s, 2)
notes(s, "Hook. Say the quote out loud. Everyone in the room has had this experience — "
         "that's the whole pitch in one sentence.")

# 3 — how people actually search
s = blank()
title_slide(s, "This is how people really look for music",
            kicker="What the research says",
            sub="Three independent studies, same finding.")
cards = [
    ("Bainbridge et al., 2003",
     "Analysed real queries posted to a music-identification forum. People describe "
     "plot, mood and context far more often than they quote lyrics correctly."),
    ("Lee, 2010",
     "Natural-language music queries are dominated by descriptive and contextual "
     "features, not bibliographic ones — people search by what a song was, not what it's called."),
    ("Hosey et al., 2019 (Spotify)",
     "When users can't name what they want, existing search fails them and they "
     "abandon the task or settle for something else."),
]
x = Inches(1.05)
for i, (who, what) in enumerate(cards):
    c = card(s, x + i * Inches(3.85), Inches(2.3), Inches(3.55), Inches(2.9))
    ctf = c.text_frame; ctf.word_wrap = True
    ctf.margin_left = ctf.margin_right = Inches(0.26); ctf.margin_top = Inches(0.26)
    para(ctf, who, size=14, bold=True, color=ACCENT, first=True)
    para(ctf, what, size=14, color=MUTED, space_before=10)
tf = textbox(s, Inches(1.05), Inches(5.6), Inches(11.4), Inches(0.9))
para(tf, "The demand is documented. The tooling never caught up.",
     size=19, bold=True, color=TEXT, first=True)
footer(s, 3)
notes(s, "Don't read the cards. Point at them and say: three separate studies, twenty years "
         "apart, all say people describe rather than name. Nobody built the search box for it.")

# 4 — prior work / gap
s = blank()
title_slide(s, "What already exists — and what it can't do",
            kicker="Prior work")
rows = [
    ["System", "Approach", "Can it take a free-text description?"],
    ["LyricsRadar (2014)", "LDA topic model over lyrics", "No — browse topics, not describe"],
    ["Lyric Jumper (2017)", "Topic-based artist profiles", "No — explore by topic"],
    ["Query-by-Blending (2019)", "Word / audio / artist vectors", "Partly — word-level, not sentences"],
    ["Spotify / Apple search", "Keyword match on metadata", "No — needs title or artist"],
    ["NoLyrics.find", "Sentence embeddings + hybrid retrieval", "Yes — that is the point"],
]
table(s, rows, Inches(1.05), Inches(2.3), Inches(11.3), Inches(2.9),
      highlight_rows=(5,),
      col_widths=[Inches(3.0), Inches(3.9), Inches(4.4)])
tf = textbox(s, Inches(1.05), Inches(5.6), Inches(11.4), Inches(0.9))
para(tf, "The gap: everything before us models topics or words. "
         "Nothing takes a whole sentence of description.",
     size=17, color=MUTED, first=True)
footer(s, 4)
notes(s, "This is the novelty claim. Prior systems are topic models and word vectors — "
         "good work, but they need you to browse, not describe.")

# 5 — what we built
s = blank()
title_slide(s, "Describe it in your own words. Get the song.",
            kicker="What we built")
tf = textbox(s, Inches(1.05), Inches(2.1), Inches(5.6), Inches(3.4))
para(tf, "You type a sentence.", size=20, bold=True, first=True)
para(tf, "The system understands what it means — not which words it contains — "
         "and returns songs whose lyrics are about the same thing.",
     size=16, color=MUTED, space_before=8)
para(tf, "84,103 songs, searchable by meaning.", size=20, bold=True, space_before=24)
para(tf, "Plus everything you'd expect from a music app: play, browse by genre, "
         "accounts, taste profile, listening history.",
     size=16, color=MUTED, space_before=8)
placeholder(s, Inches(7.2), Inches(2.1), Inches(5.1), Inches(3.5),
            "[ SCREENSHOT ]\nHome page or a results page\nwith the medals + D#/S# badges visible")
footer(s, 5)
notes(s, "Sell it here. One sentence in, the right song out. Everything technical comes after.")

# 6 — why sentence embeddings
s = blank()
title_slide(s, "Why sentence embeddings", kicker="The core decision",
            sub="The whole system rests on one idea: turn meaning into geometry.")
tf = textbox(s, Inches(1.05), Inches(2.25), Inches(5.5), Inches(3.6))
para(tf, "Every song's lyrics become a point in 384-dimensional space. "
         "Your description becomes a point too. Close together = about the same thing.",
     size=17, color=TEXT, first=True)
para(tf, "Crucially, this works with zero shared words.", size=17, bold=True,
     color=ACCENT, space_before=14)
para(tf, "“someone leaving a town for good” can match a song that never uses "
         "the words leave, town or good.", size=15, color=MUTED, space_before=8)
c = card(s, Inches(7.1), Inches(2.25), Inches(5.2), Inches(3.5))
ctf = c.text_frame; ctf.word_wrap = True
ctf.margin_left = ctf.margin_right = Inches(0.3); ctf.margin_top = Inches(0.26)
para(ctf, "Why SBERT and not plain BERT?", size=15, bold=True, color=ACCENT, first=True)
para(ctf, "BERT (Devlin et al., 2019) compares two texts by feeding them in together. "
          "To search 84,103 songs it would need 84,103 passes — per query.",
     size=14, color=MUTED, space_before=10)
para(ctf, "SBERT (Reimers & Gurevych, 2019) encodes each text once, independently, "
          "so songs are embedded ahead of time and a query becomes one vector comparison.",
     size=14, color=MUTED, space_before=10)
para(ctf, "Hours per search  →  milliseconds.", size=15, bold=True, color=GREEN, space_before=10)
footer(s, 6)
notes(s, "The BERT-vs-SBERT point is the one an examiner is most likely to probe. "
         "The answer is architectural, not accuracy: BERT cross-encodes, SBERT bi-encodes.")

# 7 — model + indexing choices
s = blank()
title_slide(s, "The engineering choices", kicker="Under the hood")
items = [
    ("all-MiniLM-L6-v2 — the embedding model",
     "6 layers, 384 dimensions, ~80MB. Runs on a laptop CPU with no GPU. Embedding all "
     "84,103 songs took about 40 minutes as a one-off; a query embeds in ~15ms. A larger "
     "model would cost more on every single search for a marginal quality gain."),
    ("PostgreSQL + pgvector — one store, not two",
     "Song metadata and the 384-dim vectors live in the same database, so similarity search "
     "is just SQL. The alternative (a separate FAISS index) means keeping two systems in sync."),
    ("Whole-song embeddings — one vector per song",
     "Each song is embedded as a single document. We deliberately did not split lyrics into "
     "chunks — see the future-work slide for why, and what we did instead."),
]
bullets(s, items, y=Inches(2.15), size=17, gap=16)
footer(s, 7)
notes(s, "Note honestly: we do NOT chunk. One vector per song. The chunking discussion is later "
         "and is a deliberate decision, not an oversight.")

# 8 — data + architecture
s = blank()
title_slide(s, "Data and architecture", kicker="How it fits together")
placeholder(s, Inches(1.05), Inches(2.15), Inches(6.9), Inches(4.0),
            "[ DIAGRAM ]\n\nquery → SBERT → vector\n              ↘\n"
            "                pgvector (dense)  ┐\n"
            "                                  ├→ RRF fusion → ranked results\n"
            "                Postgres FTS (sparse) ┘\n\n"
            "(draw this as boxes + arrows)")
tf = textbox(s, Inches(8.3), Inches(2.15), Inches(4.0), Inches(4.2))
para(tf, "music4all", size=16, bold=True, color=ACCENT, first=True)
para(tf, "84,103 English-language songs with lyrics, artist, title, album, genres, tags.",
     size=14, color=MUTED, space_before=6)
para(tf, "Song Interpretation Dataset", size=16, bold=True, color=ACCENT, space_before=18)
para(tf, "310,315 fan-written explanations of what songs mean, covering 20,672 of our songs. "
         "This is our evaluation ground truth.", size=14, color=MUTED, space_before=6)
para(tf, "Lyrics handling", size=16, bold=True, color=ACCENT, space_before=18)
para(tf, "Used to build the index only. Never redistributed — the app shows a short snippet "
         "and links to Spotify.", size=14, color=MUTED, space_before=6)
footer(s, 8)
notes(s, "Mention the copyright stance briefly — it shows you thought about it. "
         "Lyrics in, features out, snippets only.")

# 9 — how we evaluate
s = blank()
title_slide(s, "How do you prove a search engine is good?",
            kicker="Evaluation method")
tf = textbox(s, Inches(1.05), Inches(2.15), Inches(6.2), Inches(3.8))
para(tf, "We use 20,672 real fan-written interpretations as queries.", size=18, bold=True, first=True)
para(tf, "Each one explains what a song means, in a stranger's own words. "
         "We know which song it describes — so we know the right answer.",
     size=15, color=MUTED, space_before=8)
para(tf, "This is the honest version of the test: nobody wrote these to be search queries, "
         "and they never reuse the phrasing we indexed.",
     size=15, color=MUTED, space_before=10)
para(tf, "No human participants — reproducible, and light on ethics.",
     size=15, color=GREEN, space_before=12)
c = card(s, Inches(7.6), Inches(2.15), Inches(4.7), Inches(3.5))
ctf = c.text_frame; ctf.word_wrap = True
ctf.margin_left = ctf.margin_right = Inches(0.3); ctf.margin_top = Inches(0.26)
para(ctf, "What we measure", size=15, bold=True, color=ACCENT, first=True)
para(ctf, "Recall@1 / @5 / @10", size=15, bold=True, space_before=12)
para(ctf, "Did the right song appear in the top 1, 5, or 10?", size=13, color=MUTED, space_before=2)
para(ctf, "MRR", size=15, bold=True, space_before=10)
para(ctf, "How high up the list, on average.", size=13, color=MUTED, space_before=2)
para(ctf, "nDCG@10", size=15, bold=True, space_before=10)
para(ctf, "Rewards putting the answer nearer the top (Järvelin & Kekäläinen, 2002).",
     size=13, color=MUTED, space_before=2)
footer(s, 9)
notes(s, "Emphasise: these queries are hostile. Written by strangers, for a different purpose, "
         "with no overlap in phrasing. Numbers look low because the task is genuinely hard.")

# 10 — v1 + first weakness
s = blank()
title_slide(s, "Version 1: embeddings alone — and where they broke",
            kicker="First result")
tf = textbox(s, Inches(1.05), Inches(2.1), Inches(5.4), Inches(1.4))
para(tf, "Dense-only baseline", size=16, bold=True, color=MUTED, first=True)
para(tf, "nDCG@10  =  0.135", size=30, bold=True, color=TEXT, space_before=4)
para(tf, "Recall@10 = 17.6%   ·   MRR = 0.124", size=15, color=MUTED, space_before=6)
c = card(s, Inches(1.05), Inches(4.0), Inches(5.4), Inches(2.2))
ctf = c.text_frame; ctf.word_wrap = True
ctf.margin_left = ctf.margin_right = Inches(0.28); ctf.margin_top = Inches(0.24)
para(ctf, "Then I tried it by hand", size=15, bold=True, color=ACCENT, first=True)
para(ctf, "“eminem lose yourself”  →  wrong song\n"
          "“hurry hurry, step right up”  →  wrong song",
     size=15, color=TEXT, space_before=10)
para(ctf, "Embeddings understand meaning. They are bad at exact names and quoted lines.",
     size=14, color=MUTED, space_before=10)
placeholder(s, Inches(7.1), Inches(2.1), Inches(5.2), Inches(4.1),
            "[ SCREENSHOT ]\nyour dense-only failure example\n(the JSON report or a UI screenshot)")
footer(s, 10)
notes(s, "This is finding #1. The metric looked fine; using it revealed the weakness. "
         "Set up the pattern — measurement and use disagree — because it recurs later.")

# 11 — hybrid
s = blank()
title_slide(s, "Two ways to search, fused",
            kicker="The fix", sub="Semantic and literal retrieval fail in opposite directions.")
c1 = card(s, Inches(1.05), Inches(2.35), Inches(3.5), Inches(2.6))
t1 = c1.text_frame; t1.word_wrap = True
t1.margin_left = t1.margin_right = Inches(0.26); t1.margin_top = Inches(0.24)
para(t1, "DENSE", size=14, bold=True, color=BLUE, first=True)
para(t1, "SBERT embeddings", size=15, bold=True, space_before=6)
para(t1, "Understands meaning.\nMisses exact names.", size=14, color=MUTED, space_before=8)
c2 = card(s, Inches(4.9), Inches(2.35), Inches(3.5), Inches(2.6))
t2 = c2.text_frame; t2.word_wrap = True
t2.margin_left = t2.margin_right = Inches(0.26); t2.margin_top = Inches(0.24)
para(t2, "SPARSE", size=14, bold=True, color=AMBER, first=True)
para(t2, "Postgres full-text", size=15, bold=True, space_before=6)
para(t2, "Catches exact words.\nBlind to paraphrase.", size=14, color=MUTED, space_before=8)
c3 = card(s, Inches(8.75), Inches(2.35), Inches(3.55), Inches(2.6))
t3 = c3.text_frame; t3.word_wrap = True
t3.margin_left = t3.margin_right = Inches(0.26); t3.margin_top = Inches(0.24)
para(t3, "HYBRID", size=14, bold=True, color=ACCENT, first=True)
para(t3, "Reciprocal Rank Fusion", size=15, bold=True, space_before=6)
para(t3, "Merges both rankings.\nAgreement rises to the top.", size=14, color=MUTED, space_before=8)
tf = textbox(s, Inches(1.05), Inches(5.3), Inches(11.4), Inches(1.2))
para(tf, "RRF (Cormack et al., 2009) needs no score calibration — it combines positions, "
         "not scores, so two systems on totally different scales can still be merged.",
     size=15, color=MUTED, first=True)
para(tf, "Important: our sparse arm is Postgres ts_rank_cd, not BM25 — it has no IDF term. "
         "A true BM25 baseline is future work.", size=14, color=AMBER, space_before=8)
footer(s, 11)
notes(s, "Be precise here: we did NOT implement BM25. If asked why, the answer is that "
         "ts_rank_cd was already in Postgres; BM25/BM25F is the principled upgrade and is future work.")

# 12 — finding 2
s = blank()
title_slide(s, "Then the demo embarrassed me",
            kicker="Finding #2", sub="Manual testing again — this time on the finished app.")
tf = textbox(s, Inches(1.05), Inches(2.2), Inches(5.5), Inches(3.6))
para(tf, "Search: “eminem killshot”", size=19, bold=True, first=True)
para(tf, "#1   Brainless        (score 4.6)\n#2   KILLSHOT        (score 2.4)",
     size=17, color=TEXT, space_before=12)
para(tf, "The exact title match lost — to a song that doesn't contain the title at all.",
     size=15, color=MUTED, space_before=12)
para(tf, "Search: “The Cranberries Ridiculous Thoughts”", size=19, bold=True, space_before=20)
para(tf, "The exact song didn't appear in the top 20 at all.", size=15, color=MUTED, space_before=8)
placeholder(s, Inches(7.2), Inches(2.2), Inches(5.1), Inches(3.7),
            "[ SCREENSHOT ]\nyour eminem killshot / cranberries\nfailure screenshot")
footer(s, 12)
notes(s, "Tell it as a story: the app was finished, I typed a song I knew, and it was wrong. "
         "Offline evaluation had never caught this.")

# 13 — diagnosis
s = blank()
title_slide(s, "Why it happened", kicker="Diagnosis")
tf = textbox(s, Inches(1.05), Inches(2.1), Inches(5.6), Inches(3.8))
para(tf, "We weighted title and artist above lyrics — but only 2.5×.",
     size=18, bold=True, first=True)
para(tf, "That was Postgres' default, and we never questioned it.", size=15, color=MUTED, space_before=8)
para(tf, "“Brainless” says the word “Eminem” ten times:\n"
         "once as the artist, nine times inside its own lyrics.",
     size=16, color=TEXT, space_before=18)
para(tf, "“KILLSHOT” says it once, in the title.", size=16, color=TEXT, space_before=8)
para(tf, "Nine cheap mentions beat one expensive one.", size=17, bold=True,
     color=ACCENT, space_before=14)
c = card(s, Inches(7.2), Inches(2.1), Inches(5.1), Inches(3.7))
ctf = c.text_frame; ctf.word_wrap = True
ctf.margin_left = ctf.margin_right = Inches(0.3); ctf.margin_top = Inches(0.26)
para(ctf, "The fix — three changes, all query-time", size=15, bold=True, color=ACCENT, first=True)
para(ctf, "1.  Title/artist now worth 20×, not 2.5×", size=15, space_before=12)
para(ctf, "2.  Divide by song length, so long songs stop winning on volume",
     size=15, space_before=8)
para(ctf, "3.  Deterministic tie-break, so identical searches don't reshuffle",
     size=15, space_before=8)
para(ctf, "No re-indexing. No schema change. ~30 minutes of work.",
     size=14, color=GREEN, space_before=14)
footer(s, 13)
notes(s, "Mention we chose the weights by measurement, not guesswork — and that the first "
         "configuration we tried made things worse, which is why we tested four.")

# 14 — results
s = blank()
title_slide(s, "What the fix did", kicker="Results",
            sub="Same 20,672 queries, same seed, same dense model — only the ranking changed.")
rows = [
    ["System", "Recall@1", "Recall@10", "MRR", "nDCG@10"],
    ["Dense only", "0.099", "0.176", "0.124", "0.135"],
    ["Sparse — before fix", "0.007", "0.044", "0.018", "0.022"],
    ["Sparse — after fix", "0.018", "0.075", "0.035", "0.043"],
    ["Hybrid — before fix", "0.109", "0.180", "0.134", "0.142"],
    ["Hybrid — after fix", "0.115", "0.199", "0.144", "0.153"],
]
table(s, rows, Inches(1.05), Inches(2.5), Inches(11.3), Inches(2.7),
      highlight_rows=(5,),
      col_widths=[Inches(3.5), Inches(1.95), Inches(1.95), Inches(1.95), Inches(1.95)])
tf = textbox(s, Inches(1.05), Inches(5.5), Inches(11.4), Inches(1.2))
para(tf, "Sparse retrieval roughly doubled.  Hybrid gained 8% — for free, "
         "with no change to the embeddings.", size=17, bold=True, first=True)
para(tf, "We expected a trade-off: fix the short queries, lose ground on the long ones. "
         "Both improved instead.", size=15, color=MUTED, space_before=8)
footer(s, 14)
notes(s, "The honest detail worth saying: we predicted a trade-off and were wrong. "
         "Say why — 59% of sparse's wins already had the title sitting in the query text.")

# 15 — three modes
s = blank()
title_slide(s, "The system shows its own workings",
            kicker="What makes the app different",
            sub="Most search hides how it ranked. Ours doesn't.")
tf = textbox(s, Inches(1.05), Inches(2.25), Inches(5.4), Inches(3.6))
para(tf, "Every result carries its receipts.", size=18, bold=True, first=True)
para(tf, "D#1  — dense ranked it first\nS#21 — sparse ranked it twenty-first\n"
         "both  — the two retrievers agreed",
     size=16, color=TEXT, space_before=12)
para(tf, "And you can switch retrieval mode live on any results page, "
         "so the difference is visible rather than claimed.",
     size=15, color=MUTED, space_before=14)
para(tf, "For a dissertation, this is the contribution made inspectable. "
         "For a user, it's an explanation instead of a black box.",
     size=15, color=MUTED, space_before=12)
placeholder(s, Inches(7.1), Inches(2.25), Inches(5.2), Inches(3.6),
            "[ SCREENSHOT ]\nresults page showing the\ndense | sparse | hybrid toggle\n+ D#/S# badges + medals")
footer(s, 15)
notes(s, "This is your strongest app slide. Then go to the live demo.")

# 16 — stack
s = blank()
title_slide(s, "Built with", kicker="Technology")
groups = [
    ("Retrieval", "sentence-transformers (all-MiniLM-L6-v2)\nPostgreSQL 16 + pgvector\nPostgres full-text search\nReciprocal Rank Fusion"),
    ("Backend", "Python 3.11 · FastAPI\nSQLAlchemy\nJWT auth + bcrypt password hashing\nSpotify Web API (album art, playback)"),
    ("Frontend", "React 19 · Vite\nTailwind CSS v4\nReact Router\nreact-hot-toast"),
]
x = Inches(1.05)
for i, (head, body) in enumerate(groups):
    c = card(s, x + i * Inches(3.85), Inches(2.3), Inches(3.55), Inches(3.0))
    ctf = c.text_frame; ctf.word_wrap = True
    ctf.margin_left = ctf.margin_right = Inches(0.28); ctf.margin_top = Inches(0.26)
    para(ctf, head, size=15, bold=True, color=ACCENT, first=True)
    para(ctf, body, size=15, color=TEXT, space_before=12)
tf = textbox(s, Inches(1.05), Inches(5.7), Inches(11.4), Inches(0.8))
para(tf, "Accounts are fabricated test accounts only — no real personal data, "
         "so no additional ethics burden.", size=14, color=MUTED, first=True)
footer(s, 16)
notes(s, "Move fast here. One breath per column.")

# 17 — limitations / future work
s = blank()
title_slide(s, "What I'd do next", kicker="Limitations & future work")
items = [
    ("AI-written song summaries",
     "Summarise every song with an LLM and match descriptions against the summary rather than raw "
     "lyrics — closer to how people actually describe songs. Not done: 84,103 LLM calls is expensive "
     "and slow, and it adds a runtime dependency the core system deliberately avoids."),
    ("Passage-level embeddings",
     "Embed verses separately so a single memorable line isn't diluted by a whole song. Not done: "
     "~10x the vectors, plus new indexing and fusion logic. We covered the same ground differently — "
     "sparse retrieval already catches quoted lines, and whole-song embeddings still capture overall meaning."),
    ("A real BM25 baseline, and smarter fusion",
     "Our sparse arm has no IDF weighting. Also, on known-item queries hybrid can rank below sparse "
     "alone, because fusion rewards agreement and only one retriever can be right. Both are measured, "
     "documented, and next on the list."),
]
bullets(s, items, y=Inches(2.15), size=17, gap=15)
footer(s, 17)
notes(s, "Be confident that these are decisions, not omissions. Each was measured or reasoned, "
         "and the reason for not doing it is a real constraint.")

# 18 — demo
s = blank()
tf = textbox(s, Inches(1.1), Inches(2.6), Inches(11.2), Inches(2.0))
para(tf, "Live demo", size=52, bold=True, first=True)
para(tf, "nolyrics.find", size=20, color=ACCENT, space_before=10)
bar = s.shapes.add_shape(1, Inches(1.1), Inches(4.35), Inches(2.2), Inches(0.035))
bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()
bar.shadow.inherit = False
tf2 = textbox(s, Inches(1.1), Inches(4.7), Inches(11.2), Inches(1.6))
para(tf2, "Search by description  ·  dense / sparse / hybrid side by side  ·  "
          "song page and player  ·  genres  ·  account, taste profile, history",
     size=15, color=MUTED, first=True)
footer(s, 18)
notes(s, "DEMO ORDER (keep to ~4 min):\n"
         "1. Home — click an example chip, e.g. 'a song about heartbreak'.\n"
         "2. Results — point out medals and D#/S# badges.\n"
         "3. Toggle dense -> sparse -> hybrid on the SAME query. This is the money shot.\n"
         "4. Open a song — player, snippet, genres.\n"
         "5. Genres page — mosaics.\n"
         "6. Log in — taste picks, then home recommendations + history.\n"
         "BEFORE YOU START: Docker running, API up (~15s to load the model), frontend up, "
         "already logged in on a second tab as a fallback.")

# 19 — thanks
s = blank()
tf = textbox(s, Inches(1.1), Inches(2.7), Inches(11.2), Inches(1.6))
para(tf, "Thank you", size=48, bold=True, first=True)
para(tf, "Questions?", size=22, color=MUTED, space_before=12)
tf2 = textbox(s, Inches(1.1), Inches(5.5), Inches(11.2), Inches(1.2))
para(tf2, "Elvin Isayev  ·  MSc Dissertation  ·  University of Sheffield", size=14,
     color=MUTED, first=True)
footer(s, 19)
notes(s, "LIKELY QUESTIONS:\n"
         "- Why are the numbers low? 84,103 candidates, one correct answer, queries written by "
         "strangers for another purpose. Random chance is 0.001%.\n"
         "- Why not BM25? ts_rank_cd was already in Postgres; BM25/BM25F is the principled upgrade, "
         "documented as future work.\n"
         "- Why not chunk the lyrics? ~10x cost; sparse retrieval already covers quoted lines.\n"
         "- Isn't hybrid worse sometimes? Yes — on known-item queries. Measured and documented.\n"
         "- Copyright? Lyrics index the search only; the app shows snippets and links out.")

prs.save("NoLyricsFind_MockPresentation.pptx")
print("saved NoLyricsFind_MockPresentation.pptx")
print(f"slides: {len(prs.slides.__iter__.__self__._sldIdLst)}")
