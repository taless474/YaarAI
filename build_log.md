# BUILD_LOG — YaarAI (What We Built, In Order)

This document is **provenance**, not a plan. It records what was built, in order, and where each artifact lives, so every semantic field is traceable.

---

## 1) Build the corpus: scrape + prose + cleaning → JSONL

We assembled a **beyt-level** dataset with stable IDs, two **mesra**, a preserved raw string, a cleaned working string, and Ganjoor prose summaries for both the beyt and the full ghazal.

### 1.1 What we stored per record
Minimum contract per beyt:
- IDs: `poem_id`, `beyt_id`
- Beyt text:
  - `mesra_1`, `mesra_2`
  - `raw` (as captured)
  - `text` (cleaned, used for downstream processing)
- Prose context (Ganjoor insight; used as auxiliary context, never as a replacement for the verse):
  - `insight.beyt_summary`
  - `insight.ghazal_summary`
  - `insight.source_url`

### 1.2 Cleaning (before writing JSONL)
Persian text needs normalization, but poetry is sensitive to spacing and joiners (ZWNJ). Cleaning was conservative:

- Unicode NFC normalize
- remove harmful control characters (LRM/RLM, bidi overrides, isolates, Arabic Letter Mark)
- normalize Persian letter variants (e.g., `ي` becomes `ی`, `ك` becomes `ک`, etc.)
- normalize `ۀ` and `هٔ` to `ه‌ی`
- remove Arabic diacritics/tashkil
- sanitize ZWNJ/ZWJ (keep valid forms مثلِ می‌رود / ره‌رو; remove only illegal patterns)
- collapse whitespace
- apply mid-alef token fixes (e.g., `کآن` → `که آن`) via a small auditable replacement map

**Code**
- `scripts/text_cleaning.py`

### 1.3 Where raw data lives
- `data/raw/ghazals_with_insight` (JSONL)

### 1.4 Example record
```json
{"poem_id": 26, "beyt_id": 1,
"mesra_1": "زلف‌آشفته و خوی‌کرده و خندان‌لب و مست", "mesra_2": "پیرهن‌چاک و غزل‌خوان و صراحی در دست",
"raw": "زلف‌آشفته و خِوی‌کرده و خندان‌لب و مست / پیرهن‌چاک و غزل‌خوان و صُراحی در دست",
"text": "زلف‌آشفته و خوی‌کرده و خندان‌لب و مست / پیرهن‌چاک و غزل‌خوان و صراحی در دست",
"insight":
{"beyt_summary": "زلف‌های پریشان و چهره‌ای سرخوش، لبخند بر لب، بی‌خیال و سرشار از شادی، با پیرهنی تکه‌دار و غزل‌خوانی در حال شادی و مشغول نوشیدن.", "ghazal_summary": "در این شعر، شاعر به توصیف حالت شگفت‌انگیز و جذاب محبوبش می‌پردازد که با زلفی آشفته و لبانی خندان به سراغ او آمده است. او با ادای شعر و در دست داشتن جام می، عاشقانه عشق را تجلی می‌بخشد. محبوبش با شوری و حالتی غمگین به شاعر می‌گوید که خوابش سنگین شده و او را به یاد عشق واقعی می‌اندازد. شاعر به زاهدان هشدار می‌دهد که نباید بر درد عاشقان خرده بگیرند، زیرا آنها تنها تحفه عشق را در زندگی تجربه کرده‌اند. در نهایت، شاعر از توبه‌هایی که بر سر عشق می‌شکند سخن می‌گوید و زنده بودن عشق و شیدایی را جشن می‌گیرد.",
"source_url": "https://ganjoor.net/hafez/ghazal/sh26"}}
```

---

## 2) Define semantic axes

Before producing any model-derived fields, we froze the semantic interface (what fields exist, what they mean, and what constraints apply).

**Where the rules live**
- `docs/design-decisions.md`

### Current v1 semantic fields (dataset surface)
- `ghazal_axis` (ghazal-level orientation)
- `beyt_hint` (short descriptive phrase of the beyt’s meaning)
- `affect` (closed vocabulary of 8; multi-label with 0–2 tags)
- `lens` (secondary framing axis; 7 lenses; added after exploring the other semantic fields)

---

### 2.1) Embedding diagnostics: is the beyt space usable?

We used embeddings primarily to answer: does this corpus form a usable neighborhood structure for retrieval?

**Embedding model**
- `BAAI/bge-m3` (L2 normalized embeddings)

A quick “anchor neighbor” check showed semantic clustering is real, but it clusters by **register/vocabulary/theme cues** rather than directly discovering “affect” as a clean axis. That pushed us toward treating affect as a controlled label layer rather than something to infer from raw neighborhoods.

#### Anchor experiment (didn’t help with affect)

An “anchor discovery” idea was tested: pick an anchor beyt (or presumed affect word) and look at nearest neighbors to infer affect structure.

What happened:
- neighbors often grouped by register and explicit vocabulary (علم/درس/یقین/معرفت, جهان/گردون…)
- this was coherent, but it did not align with affect tags

Examples:
```text
ANCHOR (poem_id=45, beyt_id=3)
نه من ز بی‌عملی، در جهان، ملولم و بس / ملالت علما هم ز علم بی‌عمل است

NEIGHBORS

  sim=0.663 (poem_id=483, beyt_id=11)
  نه حافظ را حضور درس خلوت / نه دانشمند را علم الیقینی

  sim=0.648 (poem_id=247, beyt_id=4)
  جهان و هر چه در او هست سهل و مختصر است / ز اهل معرفت این مختصر دریغ مدار

  sim=0.646 (poem_id=363, beyt_id=7)
  اعتمادی نیست بر کار جهان / بلکه بر گردون گردان نیز هم

  sim=0.629 (poem_id=126, beyt_id=1)
  جان، بی‌جمال جانان میل جهان ندارد / هر کس که این ندارد حقا که آن ندارد

  sim=0.624 (poem_id=213, beyt_id=4)
  طالب لعل و گهر نیست وگرنه خورشید / هم‌چنان در عمل معدن و کان است که بود

==========================================================================================
ANCHOR (poem_id=472, beyt_id=1)
احمد الله علی معدلة السلطان / احمد شیخ اویس حسن ایلخانی

NEIGHBORS

  sim=0.521 (poem_id=460, beyt_id=4)
  ربیع العمر فی مرعی حماکم / حماک الله یا عهد التلاقی

  sim=0.509 (poem_id=460, beyt_id=5)
  بیا ساقی بده رطل گرانم / سقاک الله من کاس دهاق

  sim=0.507 (poem_id=463, beyt_id=1)
  سلام الله ما کر اللیالی / و جاوبت المثانی و المثالی

  sim=0.501 (poem_id=408, beyt_id=3)
  در اوج ناز و نعمتی ای پادشاه حسن / یا رب مباد تا به قیامت زوال تو

  sim=0.498 (poem_id=473, beyt_id=12)
  جمع کن به احسانی حافظ پریشان را / ای شکنج گیسویت مجمع پریشانی
```

Takeaway:
- affect works better as a controlled layer (curated vocabulary + constrained tagging + validation), not something inferred from anchor neighborhoods.

An initial affect vocabulary was drafted based on reading and interpretation experience with Hafez:

```python
AFFECT_VOCAB = [
    "شادی", "اندوه", "دلتنگی", "امید", "ناامیدی",
    "حیرت", "آرامش", "بی‌قراری", "اعتراض", "رضایت"
]
```
---

### 2.2) Local model attempts

Local/open instruct models were tested for producing `beyt_hint` + constrained affect tags, including:

- `MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"` didn't have enough RAM to build this

A smaller model was then tested:

- `MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"`

The failure modes were consistent:
- off-target `beyt_hint` phrasing (or stylistically wrong for the intended use)
- frequent invalid affect outputs (often empty or drifted labels)

Examples (failure mode snapshot):
```text
beyt PROSE: ای زاهد، تو برو و به می‌نوشان ایراد نگیرید؛ زیرا در روز الست، تنها همین نعمت نصیب ما شد.
beyt_hint: نقمت‌های فردی غیرمعتمد
affect: []

beyt PROSE:  ما هر چه را که او به پیمانهٔ ما ریخت، نوشیدیم؛ خواه آن نوشیدنی از شراب بهشت باشد یا از شراب مستی.
beyt_hint: شراب‌های بین‌المللی بازخورد
affect: []

beyt PROSE: خندهٔ شراب و زلف پیچیدهٔ معشوق، باعث می‌شود که بسیاری از توبه‌ها مانند توبهٔ حافظ زیر پا قرار گیرد و شکسته شود.
beyt_hint: پیچیدگی عاطفی
affect: []

beyt PROSE: فدای پیراهن پاره و زیبای دختران ماهرو شوم، حتی اگر برای این کار هزار لباس پرهیز و تقوا داشته باشم.
beyt_hint: تبدیل به عکس ماهربا
affect: []

beyt PROSE: بیا که دیروز صدای میخانه به من گفت که در حالت آرامش و رضا قرار بگیر و از سرنوشت فرار نکن.
beyt_hint: مکالمات آرامش و رضا
affect: []
```

**Decision**
We switched to an API model for annotation with deterministic settings (temperature=0).

---

### 2.3) Use API to derive `ghazal_axis` + validate

We produced a ghazal-level label `ghazal_axis` (one per ghazal; attached to all beyts in that ghazal).

**Inputs**
- full ghazal text + `insight.ghazal_summary`

**Output**
- `ghazal_axis` (short phrase capturing global orientation)

**Extraction code**
- `scripts/extract_ghazal_axis.py`

**Validation**
- `notebooks/01_validate_ghazal_axis.ipynb`

Recap: some axes were long; when they were found, they were not modified in-place. Examples:

```
8 → تغییر و دگرگونی در پیوندهای انسانی و معنوی
8 → جستجوی حقیقت و معرفت در پیوند با عشق
9 → پیوند مراتب وجودی و تمایز میان ظاهر و باطن
10 → پیوند رمز و نشانه‌های کیهانی با مفاهیم وفا و معرفت
8 → جستجوی کمال و معنا در پیوند با معشوق
8 → جستجوی معنای پایدار در پیوند انسانی و الهی
8 → جستجوی حقیقت در پیوند با معشوق و می
```

One axis also appeared repeatedly:
```
[('جستجوی حقیقت پنهان', 12),
 ('ناپایداری جهان', 4),
 ('تمایز حقیقت و ظاهر', 4),
 ('تقابل ظاهر و باطن', 4),
 ('جستجوی وصال', 4),
 ('جستجوی حقیقت مطلق', 3),
 ('کشمکش درونی', 2),
 ('پایداری پیوند معنوی', 2),
 ('مرکزیت معشوق', 2),
 ('پیوند ناپیدای دل و معشوق', 2),
 ('جستجوی پیوند معنوی', 2),
 ('پیوند ناپیدای عاشق و معشوق', 2),
 ('جستجوی کمال', 2),
 ('جدایی و پیوستگی', 2),
 ('ناپایداری دستاوردها', 2),
 ('پیچیدگی روابط انسانی', 2),
 ('ترک تعلقات دنیوی', 2),
 ('جدایی و بی‌اعتنایی', 2),
 ('جستجوی حقیقت درونی', 2),
 ('ناپایداری فرصت‌ها', 2)]
```

That repeated axis was scrutinized against full ghazals:
```
poem_id = 7
AXIS: جستجوی حقیقت پنهان
beytS:
- صوفی بیا که آینه، صافی‌ست جام را / تا بنگری صفای می لعل‌فام را
- راز درون پرده ز رندان مست پرس / کاین حال نیست زاهد عالی‌مقام را
- عنقا، شکار کس نشود، دام بازچین / که آنجا، همیشه، باد به دست است، دام را
- در بزم دور، یک‌دو قدح درکش و برو / یعنی طمع مدار وصال مدام را
- ای دل! شباب رفت و نچیدی گلی ز عیش / پیرانه‌سر مکن هنری ننگ و نام را
- در عیش نقد کوش که چون آبخور نماند / آدم بهشت، روضه‌ی دارالسلام را
- ما را بر آستان تو، بس حق خدمت است / ای خواجه! بازبین به ترحم غلام را
- «حافظ» مرید جام می است، ای صبا! برو! / وز بنده بندگی برسان شیخ جام را!
============================================================
poem_id = 19
AXIS: جستجوی حقیقت پنهان
beytS:
- ای نسیم سحر آرامگه یار کجاست؟ / منزل آن مه عاشق‌کش عیار کجاست؟
- شب تار است و ره وادی ایمن در پیش / آتش طور کجا موعد دیدار کجاست؟
- هر که آمد به جهان نقش خرابی دارد / در خرابات بگویید که هشیار کجاست؟
- آن‌کس است اهل بشارت که اشارت داند / نکته‌ها هست بسی محرم اسرار کجاست؟
- هر سر موی مرا با تو هزاران کار است / ما کجاییم و ملامت‌گر بی‌کار کجاست؟
- باز پرسید ز گیسوی شکن در شکنش / کاین دل غم‌زده سرگشته گرفتار کجاست؟
- عقل دیوانه شد آن سلسله‌ی مشکین کو؟ / دل ز ما گوشه گرفت ابروی دلدار کجاست؟
- ساقی و مطرب و می جمله مهیاست ولی / عیش بی‌یار مهیا نشود یار کجاست؟
- حافظ از باد خزان در چمن دهر مرنج / فکر معقول بفرما گل بی‌خار کجاست؟
============================================================
poem_id = 81
AXIS: جستجوی حقیقت پنهان
beytS:
- صبحدم، مرغ چمن با گل نوخاسته گفت / ناز، کم کن که در این باغ، بسی چون تو شکفت
- گل بخندید که از راست نرنجیم ولی / هیچ عاشق، سخن سخت به معشوق نگفت
- گر طمع داری از آن جام مرصع، می لعل / ای بسا در که به نوک مژه‌ات باید سفت
- تا ابد، بوی محبت به مشامش نرسد / هر که خاک در میخانه به رخساره نرفت
- در گلستان ارم، دوش، چو از لطف هوا / زلف سنبل به نسیم سحری می‌آشفت
- گفتم: «ای مسند جم! جام جهان‌بینت کو؟» / گفت: «افسوس که آن دولت بیدار بخفت!»
- سخن عشق، نه آن است که آید به زبان / ساقیا، می ده و کوتاه کن این گفت و شنفت
- اشک «حافظ»، خرد و صبر به دریا انداخت / چه کند؟ سوز غم عشق نیارست نهفت
```
Given Hafez’s themes, it made sense that many ghazals legitimately fall under “pursuing the hidden truth.”

---

### 2.4) Enforce affect vocabulary and produce beyt annotations

We finalized an 8-label affect vocabulary:

```python
AFFECT_VOCAB = [
  "اندوه",
  "امید",
  "ناامیدی",
  "حیرت",
  "شوق",
  "حسرت",
  "آرامش",
  "بی‌قراری",
]
```
| Affect (FA) | Gloss (EN) |
|---|---|
| اندوه | sorrow |
| امید | hope |
| ناامیدی | despair |
| حیرت | wonder |
| شوق | yearning |
| حسرت | regret |
| آرامش | calm |
| بی‌قراری | restlessness |


Rules:
- affect must be chosen only from `AFFECT_VOCAB`
- cardinality per beyt: `len(affect) ∈ {0,1,2}`

Operational guard:
- if the model outputs an affect not in the list, we re-ask
- rejected values are logged for audit

**Rejected affects**
- `data/logs/rejected_affects_v1.jsonl`

Then we produced beyt-level annotations:

**Inputs (per beyt)**
- beyt text (two mesra)
- `insight.beyt_summary`
- `ghazal_axis`
- `AFFECT_VOCAB`

**Outputs**
- `beyt_hint` (short descriptive phrase; non-directive)
- `affect` (0–2 tags from `AFFECT_VOCAB`)

**Extraction code**
- `scripts/extract_beyt_annotations.py`

**Annotation artifact**
- `data/annotations/beyt_annotations_v1.jsonl` (and subsequent versions)

---

### 2.5) Validate beyt annotations

Validation goals:
- schema correctness
- distribution sanity
- repair traceability (no silent overwrite)
- qualitative spot checks with full context

#### beyt_hint quality/normalization iterations
Instead of overwriting, we versioned refinements.

Key fixes:
- **Conciseness repair** for overly long hints
  Code: `scripts/repair_beyt_hints.py`
  Prompt: `prompts/repair_prompts_v1.py`
- **Directive normalization** (remove “دعوت به…/توصیه به…/تشویق به…” style framing)
  Code: `scripts/normalize_directive_beyt_hints.py`

The end state: **fully descriptive, non-directive** `beyt_hint` strings.

**Annotation artifact**
- `data/annotations/beyt_annotations_v1_3.jsonl` (the last sub version)

#### Affect inspection (distribution + cardinality)
Example distribution snapshot:
```
Counter({
  'حسرت': 1483,
  'شوق': 1251,
  'امید': 752,
  'اندوه': 751,
  'بی‌قراری': 538,
  'آرامش': 450,
  'حیرت': 398,
  'ناامیدی': 113
})
```

Cardinality:
```
Counter({1: 2056, 2: 1840, 0: 296})
```

---

## 3) Diving deep into current semantic axes

This phase is where we treated the annotation space as an object we can test: probe design, embeddings, PCA, cohesion, UMAP sweeps, and quantitative label sanity.

---

### 3.1) Defining probes and computing embeddings

We used probe strings as **evaluation representations** (not necessarily what the product must embed).

Probes:
- `probe_hint_only = beyt_hint`
- `probe_hint_affect = beyt_hint | affect_1، affect_2` (omit affect if empty)

(We deliberately exclude `ghazal_axis` from cohesion probes to avoid leaking poem identity into diagnostics; see 3.3.)

Embeddings:
- `SentenceTransformer("BAAI/bge-m3")`
- `normalize_embeddings=True`

**Embedding code**
- `scripts/embed_beyts.py`

**Persisted artifacts**
- `data/embeddings/... .parquet` (IDs + embedding columns)

---

### 3.2) PCA

We ran PCA to quantify intrinsic dimensionality (diagnostic only).

Example PCA results on main embedding matrix:
- k80 ≈ 120
- k90 ≈ 203
- k95 ≈ 287

PCA was used as measurement and for some downstream analyses, not as “the embedding.”

---

### 3.3) Ghazal cohesion

We measured kNN same-ghazal neighbor rate (k=20):
- For each beyt, compute fraction of its top-k neighbors with the same `poem_id`.
- Compare to a random baseline.

Important: cohesion depends on *what you embed*. We keep two facts separate:

1) **Cohesion when ghazal identity leaks into the representation** can look artificially high (not what we want to evaluate).
2) **Cohesion on evaluation probes that exclude `ghazal_axis`** is intentionally weak (median 0), supporting beyt-level independence.

Results used for “beyt-first” probes (k=20):
- hint-only: mean ≈ 0.008–0.009, median 0
- hint|affect: mean ≈ 0.008–0.009, median 0
- baseline ≈ 0.0019–0.0022

Interpretation:
- Most beyts have 0 same-ghazal neighbors in top-20 under these probes.
- That matches the product stance: ghazals move across situations; we don’t want poem membership to dominate retrieval geometry.

---

### 3.4) UMAP parameter sweep

UMAP was used as a visualization sanity check, not proof.

We ran a parameter sweep and compared runs via trustworthiness (local neighborhood preservation). Then we picked a “story” setting for readability (e.g., `n_neighbors=30, min_dist=0.1`) while keeping the sweep outputs for provenance.

Artifacts:
- plots: `assets/plots/...`
- sweep tables/notes: `data/reports/03_probe_and_embed/`

---

### 3.5) Affect labels and kNN coherence

We computed a multi-label-safe kNN coherence metric:

- For each beyt, fraction of k nearest neighbors that share **at least one** affect label.
- Compare to a shuffle baseline (permute affect sets across beyts; keep geometry fixed).

Key outcome:
- hint|affect neighborhoods were ~**3×** more enriched than shuffled for shared affect (strong evidence affect labels align with local semantic neighborhoods when included in the probe).
- hint-only is weaker (as expected).

---

### 3.6) Affect centroid diagnostics

We computed per-affect centroids (mean embedding vectors) and used:
- centroid–centroid cosine similarity
- within-affect tightness (mean cosine to centroid)

This showed “families” of close affects (expected in Hafez; not a reason to delete labels), and helped explain overlap seen in UMAP facets.

Artifacts:
- `assets/plots/affect_centroid_...png`
- `data/reports/03_probe_and_embed/...`

---

### 3.7) Possibility of another axis: lenses (evidence → formalization)

#### Why we looked for this
Affect (۸گانه) captures “how it feels,” but not necessarily “what semantic/rhetorical move the beyt is making.” Many beyts share affect but differ sharply in stance/structure.

#### Evidence from clustering annotated theme text
We clustered **annotated semantic text** rather than raw verse:

- `theme_text = beyt_hint | ghazal_axis`
- embedding: bge-m3 (normalized) + PCA
- clustering: HDBSCAN on a large generic manifold subset (high noise is expected in poetry)

Outcome: the “ocean” split into coherent subthemes (non-noise subclusters) such as:
- admiration/beauty/perfection
- hidden truth / seeking the concealed
- return / waiting / hope
- relational indifference / asymmetry
- motif clusters (دل–زلف)
- ظاهر/باطن (appearance vs inner truth)
- seeking union / failure

These were not just affect buckets; they mixed affects and organized by semantic/rhetorical structure.

#### Formalization: 7 lenses (v1)
We defined a controlled lens set (7), recorded in `scripts/config.py`:

- soft: انتظار، فاصله، گلایه، پذیرش، حیرت معرفتی
- hard: ریا، ناپایداری جهان

Lenses are intended to capture stance/angle beyond affect.

#### Validation status + next step
- Current lenses have been validated via scoring/diagnostics already in the repo.
- I manually labeled ~130 beyts and attempted softmax training on embeddings, then concluded the label set needs to grow before supervised calibration is reliable.
- Next version: I will expand labels (target low-margin items first) and optionally tweak lens definitions before retraining.

---

## Appendix: where the main v1 product lives
We keep v1 scripts working as the product surface:
- `scripts/fal_assembly.py`
- `scripts/retrieval.py`
- `scripts/test_fal.py`
