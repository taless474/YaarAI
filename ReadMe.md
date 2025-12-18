    # YaarAI — Semantic Hafez Dataset

    YaarAI is a curated semantic annotation dataset for the poetry of Hafez,
    designed to support high-fidelity embedding-based retrieval, semantic search,
    and contextual analysis.

    The project focuses on semantic structure, not poetry generation or stylistic
    imitation. All annotations are grounded in authentic Hafez bayts and validated
    through a conservative, engineering-style pipeline.

    The dataset will be published on Hugging Face for public research and
    educational use.

    --------------------------------------------------------------------

    WHAT THIS REPOSITORY CONTAINS

    Source material:
    - ~4,200 authentic Hafez Ghazal bayts
    - Each bayt includes:
      * poem_id
      * bayt_id
      * text (two hemistichs combined)
      * bayt_prose — modern Persian explanation of the bayt
      * ghazal_prose — modern Persian explanation of the whole ghazal

    Prose explanations are derived from Ganjoor and are used only as semantic
    grounding.

    --------------------------------------------------------------------

    SEMANTIC ANNOTATIONS (CORE CONTRIBUTION)

    Ghazal axis (ghazal_axis):
    A short abstract noun phrase describing the central semantic axis of the ghazal.

    Constraints:
    - Persian only
    - One abstract noun phrase
    - No verbs
    - No emotional words
    - Applicable across multiple bayts

    Example:
    "ghazal_axis": "تمایز حقیقت و ظاهر"

    --------------------------------------------------------------------

    Bayt hint (bayt_hint):
    A short noun phrase describing what is happening in the bayt.

    Constraints:
    - Persian only
    - Neutral and descriptive
    - No verbs
    - No explanation or moralizing
    - No interpretive commentary

    Example:
    "bayt_hint": "درخواست جام از ساقی"

    --------------------------------------------------------------------

    Affect (affect):
    A controlled vocabulary capturing directly present emotion, if any.
    Each bayt may have zero, one, or two affects.

    Affect vocabulary (v1.0):
    اندوه، امید، ناامیدی، حیرت، شوق، حسرت، آرامش، بی‌قراری

    Notes:
    - Empty list is allowed
    - Affect is annotated conservatively
    - No inferred or speculative emotion

    --------------------------------------------------------------------

    ANNOTATION METHODOLOGY

    Model:
    - GPT-4.1 (via OpenAI API)

    Decoding:
    - Deterministic (temperature = 0, fixed seed)

    Pipeline characteristics:
    - Resume-safe
    - Rate-limit aware
    - Schema-validated
    - One-time preprocessing (not a live service)

    Prompting strategy:
    - Persian prompts for semantic abstraction
    - English prompts for constrained repair and normalization
    - Persian-only outputs

    No poetry generation occurs at any stage.

    --------------------------------------------------------------------

    REPAIR AND CURATION STEP (BAYT ANNOTATIONS v1.1)

    During validation, a subset of bayt-level annotations showed interpretive or
    didactic drift (for example phrases starting with "توصیه به ..." or
    "پند اخلاقی ...").

    A constrained repair pass was applied:
    - Only bayts with long hints (more than 8 tokens) were eligible
    - A deterministic repair prompt removed advice, moralizing, and explanatory tone
    - Core semantic content was preserved
    - No new meaning was introduced

    Repaired entries are explicitly marked in metadata:
    "repair": true
    "repair_rule": "bayt_hint_len>8"

    Original annotations are preserved.


    --------------------------------------------------------------------

    INTENDED USE

    This dataset is designed for:
    - Semantic embeddings
    - Cosine-similarity retrieval
    - Fal-e-Hafez systems
    - Clustering and thematic analysis
    - Contextual exploration of Hafez’s poetry

    It is NOT intended for:
    - Poetry generation
    - Paraphrasing Hafez
    - Stylistic imitation

    --------------------------------------------------------------------

    CURRENT STATUS

    - Ghazal axes validated
    - Bayt hints validated
    - Affect distribution validated
    - Semantic layer frozen

    Next step:
    - Build embeddings (e.g. bge-m3)
    - Evaluate whether a meaningful Hafez semantic space emerges
    - Publish the dataset on Hugging Face

    --------------------------------------------------------------------

    DESIGN PHILOSOPHY

    - Accuracy over creativity
    - Restraint over verbosity
    - Consistency over novelty
    - Human judgment over blind automation

    The goal is not to reinterpret Hafez, but to index meaning without distorting it.

    --------------------------------------------------------------------

    LICENSE AND ATTRIBUTION

    - Hafez’s poetry: public domain
    - Prose explanations: derived from Ganjoor (used for semantic grounding only)
    - Semantic annotations: released for research and educational use

    License to be specified before Hugging Face release.

    --------------------------------------------------------------------

    CITATION

    If you use this dataset, please cite:

    YaarAI — Semantic Hafez Dataset
    Curated semantic annotations for Persian classical poetry

    Full citation will be added with the Hugging Face release.
