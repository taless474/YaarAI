    # scripts/test_fal.py

from scripts.fal_assembly import assemble_fal
from scripts.language.affect_variants import AFFECT_VARIANTS
from scripts.language.lens_soft import LENS_VARIANTS_SOFT
from scripts.language.lens_hard import LENS_VARIANTS_HARD

def main():
    row = {
        "poem_id": 1,
        "bayt_id": 1,
        "text": "واعظان کاین جلوه در محراب و منبر می‌کنند / چون به خلوت می‌روند آن کار دیگر می‌کنند",
        "affect": ["حیرت"],
        "lens": "ریا",
    }

    out = assemble_fal(
        row,
        affect_variants=AFFECT_VARIANTS,
        lens_soft=LENS_VARIANTS_SOFT,
        lens_hard=LENS_VARIANTS_HARD,
    )

    print("\n--- Fal Output ---\n")
    print(out)


if __name__ == "__main__":
    main()
