# scripts/train_softmax_8class.py
# Train a calibrated softmax classifier for lenses (supports 8 classes incl. None).
#
# Works with:
#   - labeled CSV/JSONL containing: poem_id, beyt_id, text (or alternatives), human_lens
#   - embeddings file (parquet/csv/jsonl) keyed by poem_id,beyt_id with column "embedding"
#
# Key fixes vs your crashing version:
#   1) CSV read keeps literal "None" as a string (won't be swallowed as NaN)
#   2) Robust split: forces rare classes into TRAIN and ensures every class exists in TRAIN
#   3) Safe temperature scaling: aligns y indices with the model's actual class columns
#   4) Accepts embeddings stored as numpy arrays, lists, or JSON-stringified lists

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, log_loss
from sklearn.model_selection import train_test_split


# -----------------------------
# IO helpers
# -----------------------------
def read_labeled(path: str, none_label: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p.resolve())

    suf = p.suffix.lower()
    if suf == ".csv":
        # IMPORTANT: keep_default_na=False so literal "None" stays a string
        df = pd.read_csv(p, keep_default_na=False)
    elif suf in (".jsonl", ".json"):
        df = pd.read_json(p, lines=True)
    else:
        raise ValueError(f"Unsupported labeled file extension: {p.suffix}")

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    # Drop garbage unnamed columns created by spreadsheets
    unnamed = [c for c in df.columns if c.lower().startswith("unnamed:")]
    if unnamed:
        df = df.drop(columns=unnamed)

    required = {"poem_id", "beyt_id", "human_lens"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in labeled file: {missing}. Columns: {list(df.columns)}")

    # Text column normalization
    if "text" not in df.columns:
        for c in ["beyt", "beyt_text", "fa_text", "run3_pred__text"]:
            if c in df.columns:
                df = df.rename(columns={c: "text"})
                break
    if "text" not in df.columns:
        # Not strictly needed for embedding-based training, but keep for debugging
        df["text"] = ""

    # Normalize ids
    df["poem_id"] = df["poem_id"].astype(int)
    df["beyt_id"] = df["beyt_id"].astype(int)

    # Normalize labels
    df["human_lens"] = df["human_lens"].astype(str).str.strip()
    # empty -> NA, but keep literal none_label
    df.loc[df["human_lens"] == "", "human_lens"] = pd.NA

    # Normalize "None" variants to the exact none_label
    # (covers None/none/NONE, etc. without affecting Persian labels)
    df.loc[df["human_lens"].str.lower() == none_label.lower(), "human_lens"] = none_label

    # Normalize text (optional)
    df["text"] = df["text"].astype(str)
    df.loc[df["text"].str.strip().isin(["", "nan"]), "text"] = pd.NA

    df = df.drop_duplicates(["poem_id", "beyt_id"], keep="first").copy()
    return df


def _to_vec(x) -> Optional[np.ndarray]:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    if isinstance(x, np.ndarray):
        return x.astype(np.float32, copy=False)
    if isinstance(x, list):
        return np.asarray(x, dtype=np.float32)
    if isinstance(x, str):
        try:
            v = json.loads(x)
            if isinstance(v, list):
                return np.asarray(v, dtype=np.float32)
        except Exception:
            return None
    return None


def attach_embeddings(df: pd.DataFrame, emb_path: Optional[str], emb_col: str = "embedding") -> pd.DataFrame:
    """
    If df already has emb_col, keep it.
    Else load embeddings from emb_path keyed by poem_id,beyt_id and merge.
    """
    if emb_col in df.columns:
        return df

    if not emb_path:
        raise RuntimeError(f"Labeled file has no '{emb_col}' column and no --embeddings_path provided.")

    p = Path(emb_path)
    if not p.exists():
        raise FileNotFoundError(p.resolve())

    suf = p.suffix.lower()
    if suf == ".parquet":
        emb = pd.read_parquet(p)
    elif suf == ".csv":
        emb = pd.read_csv(p, keep_default_na=False)
    elif suf in (".jsonl", ".json"):
        emb = pd.read_json(p, lines=True)
    else:
        raise ValueError(f"Unsupported embeddings file extension: {p.suffix}")

    emb.columns = [c.strip() for c in emb.columns]

    for c in ["poem_id", "beyt_id", emb_col]:
        if c not in emb.columns:
            raise ValueError(f"Embeddings file missing '{c}'. Columns: {list(emb.columns)}")

    emb["poem_id"] = emb["poem_id"].astype(int)
    emb["beyt_id"] = emb["beyt_id"].astype(int)

    emb = emb.drop_duplicates(["poem_id", "beyt_id"], keep="first")[["poem_id", "beyt_id", emb_col]]
    out = df.merge(emb, on=["poem_id", "beyt_id"], how="left")

    if out[emb_col].isna().any():
        missing_n = int(out[emb_col].isna().sum())
        missing_rows = out[out[emb_col].isna()][["poem_id", "beyt_id"]].head(10).to_dict("records")
        raise RuntimeError(
            f"Missing embeddings for {missing_n} labeled rows after merge. "
            f"Example missing keys: {missing_rows}"
        )
    return out


def build_X(df: pd.DataFrame, emb_col: str = "embedding") -> np.ndarray:
    vecs = []
    for v in df[emb_col].tolist():
        vv = _to_vec(v)
        if vv is None:
            raise RuntimeError(f"Could not parse an embedding value: {type(v)}")
        vecs.append(vv)
    return np.vstack(vecs)


# -----------------------------
# Split helpers (robust for rare classes)
# -----------------------------
def _force_all_classes_in_train(
    df_tr: pd.DataFrame, y_tr: np.ndarray,
    df_va: pd.DataFrame, y_va: np.ndarray,
    df_te: pd.DataFrame, y_te: np.ndarray,
    all_classes: np.ndarray,
    rng: np.random.Generator
) -> Tuple[pd.DataFrame, np.ndarray, pd.DataFrame, np.ndarray, pd.DataFrame, np.ndarray]:
    """
    Ensure every class in all_classes appears at least once in TRAIN.
    If missing, move one example of that class from VAL (else TEST) into TRAIN.
    """
    present = set(np.unique(y_tr).tolist())
    missing = [c for c in all_classes.tolist() if c not in present]
    if not missing:
        return df_tr, y_tr, df_va, y_va, df_te, y_te

    for c in missing:
        moved = False
        # try from val
        idxs = np.where(y_va == c)[0]
        if len(idxs) > 0:
            pick = int(rng.choice(idxs))
            df_tr = pd.concat([df_tr, df_va.iloc[[pick]]], axis=0)
            y_tr = np.concatenate([y_tr, [y_va[pick]]])
            df_va = df_va.drop(df_va.index[pick]).reset_index(drop=True)
            y_va = np.delete(y_va, pick)
            moved = True
        else:
            # try from test
            idxs = np.where(y_te == c)[0]
            if len(idxs) > 0:
                pick = int(rng.choice(idxs))
                df_tr = pd.concat([df_tr, df_te.iloc[[pick]]], axis=0)
                y_tr = np.concatenate([y_tr, [y_te[pick]]])
                df_te = df_te.drop(df_te.index[pick]).reset_index(drop=True)
                y_te = np.delete(y_te, pick)
                moved = True

        if not moved:
            # This means the class doesn't exist outside train either (shouldn't happen)
            pass

    df_tr = df_tr.reset_index(drop=True)
    return df_tr, y_tr, df_va, y_va, df_te, y_te


def split_robust(
    df: pd.DataFrame,
    X: np.ndarray,
    y: np.ndarray,
    test_size: float,
    val_size: float,
    seed: int,
    min_count_for_strat: int = 3,
) -> Tuple[Tuple[np.ndarray, np.ndarray, pd.DataFrame],
           Tuple[np.ndarray, np.ndarray, pd.DataFrame],
           Tuple[np.ndarray, np.ndarray, pd.DataFrame]]:
    """
    Robust split for small datasets:
      - Any class with < min_count_for_strat is forced entirely into TRAIN.
      - Remaining data is split stratified into train/val/test.
      - Finally, ensure every class appears in TRAIN.
    """
    rng = np.random.default_rng(seed)

    counts = pd.Series(y).value_counts()
    rare_classes = counts[counts < min_count_for_strat].index.to_numpy()

    rare_mask = np.isin(y, rare_classes)
    df_rare, X_rare, y_rare = df[rare_mask].copy(), X[rare_mask], y[rare_mask]
    df_common, X_common, y_common = df[~rare_mask].copy(), X[~rare_mask], y[~rare_mask]

    if len(rare_classes) > 0:
        print("Rare classes forced into TRAIN (class_id -> count):",
              {int(k): int(v) for k, v in counts[counts < min_count_for_strat].to_dict().items()})

    # If common part is too small or stratify would fail, fall back to non-stratified
    can_stratify_common = True
    if len(np.unique(y_common)) < 2:
        can_stratify_common = False
    else:
        # stratify requires each class have >=2 for a split; we already removed <min_count_for_strat,
        # but with tiny data, it can still fail depending on split ratios. We'll catch exceptions.
        can_stratify_common = True

    try:
        X_trval, X_te, y_trval, y_te, df_trval, df_te = train_test_split(
            X_common, y_common, df_common,
            test_size=test_size,
            random_state=seed,
            stratify=y_common if can_stratify_common else None
        )
        X_tr, X_va, y_tr, y_va, df_tr, df_va = train_test_split(
            X_trval, y_trval, df_trval,
            test_size=val_size,
            random_state=seed,
            stratify=y_trval if can_stratify_common else None
        )
    except Exception as e:
        print("WARNING: stratified split failed; falling back to random split. Reason:", repr(e))
        X_trval, X_te, y_trval, y_te, df_trval, df_te = train_test_split(
            X_common, y_common, df_common, test_size=test_size, random_state=seed, stratify=None
        )
        X_tr, X_va, y_tr, y_va, df_tr, df_va = train_test_split(
            X_trval, y_trval, df_trval, test_size=val_size, random_state=seed, stratify=None
        )

    # Add rare to train
    if len(df_rare) > 0:
        X_tr = np.vstack([X_tr, X_rare]) if len(X_tr) > 0 else X_rare
        y_tr = np.concatenate([y_tr, y_rare]) if len(y_tr) > 0 else y_rare
        df_tr = pd.concat([df_tr, df_rare], axis=0)

    df_tr = df_tr.reset_index(drop=True)
    df_va = df_va.reset_index(drop=True)
    df_te = df_te.reset_index(drop=True)

    # Ensure every class appears in train
    all_classes = np.unique(y)
    df_tr, y_tr, df_va, y_va, df_te, y_te = _force_all_classes_in_train(
        df_tr, y_tr, df_va, y_va, df_te, y_te, all_classes, rng
    )

    # Rebuild X arrays from original X slices is hard after moving rows; easiest is to return indices-free dataframes
    # We'll also return X_tr/X_va/X_te computed by selecting rows in df_* from the master df is not stable due to copies.
    # So: store embeddings in df and rebuild X per split.
    return (df_tr, y_tr), (df_va, y_va), (df_te, y_te)


# -----------------------------
# Metrics + calibration
# -----------------------------
def softmax(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(z)
    return exp / exp.sum(axis=1, keepdims=True)


def topk_acc(probs: np.ndarray, y: np.ndarray, k: int = 1) -> float:
    topk = np.argsort(-probs, axis=1)[:, :k]
    return float((topk == y[:, None]).any(axis=1).mean())


def multiclass_brier(probs: np.ndarray, y: np.ndarray, n_classes: int) -> float:
    Y = np.eye(n_classes)[y]
    return float(np.mean(np.sum((probs - Y) ** 2, axis=1)))


def ece(probs: np.ndarray, y: np.ndarray, n_bins: int = 10) -> float:
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    acc = (pred == y).astype(float)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    out = 0.0
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (conf > lo) & (conf <= hi) if i > 0 else (conf >= lo) & (conf <= hi)
        if mask.sum() == 0:
            continue
        out += float(mask.mean()) * abs(float(acc[mask].mean()) - float(conf[mask].mean()))
    return float(out)


@dataclass
class TemperatureScaler:
    T: float = 1.0

    def fit(self, logits: np.ndarray, y: np.ndarray, lr: float = 0.01, max_iter: int = 2000):
        """
        logits: [N, C] aligned to class ids 0..C-1
        y: [N] with values in 0..C-1
        """
        T = 1.0
        n = logits.shape[0]
        for _ in range(max_iter):
            scaled = logits / T
            p = softmax(scaled)
            exp_logit = (p * logits).sum(axis=1)
            true_logit = logits[np.arange(n), y]
            grad = np.mean((exp_logit - true_logit) / (T ** 2))
            T_new = float(np.clip(T - lr * grad, 0.05, 20.0))
            if abs(T_new - T) < 1e-7:
                break
            T = T_new
        self.T = float(T)
        return self

    def proba(self, logits: np.ndarray) -> np.ndarray:
        return softmax(logits / self.T)


# -----------------------------
# Main
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled_path", required=True)
    ap.add_argument("--embeddings_path", default=None)
    ap.add_argument("--emb_col", default="embedding")
    ap.add_argument("--none_label", default="None")
    ap.add_argument("--out_model", default="models/softmax_8class.joblib")
    ap.add_argument("--out_report", default="reports/softmax_8class_report.md")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--test_size", type=float, default=0.20)
    ap.add_argument("--val_size", type=float, default=0.20)
    ap.add_argument("--class_weight", default="balanced", choices=["balanced", "none"])
    ap.add_argument("--min_count_for_strat", type=int, default=3)
    args = ap.parse_args()

    # Load + merge embeddings
    df = read_labeled(args.labeled_path, none_label=args.none_label)
    df = attach_embeddings(df, args.embeddings_path, emb_col=args.emb_col)

    # Keep labeled rows only
    df = df.dropna(subset=["human_lens"]).copy()

    # Show counts (this will tell you immediately whether None is being detected)
    vc = df["human_lens"].value_counts()
    print("Label counts:\n", vc.to_string())

    # Build label set from PRESENT labels only (no forcing).
    # If None exists, it'll be included.
    labels = sorted(df["human_lens"].unique().tolist())
    if args.none_label not in labels:
        print(f"WARNING: '{args.none_label}' not detected as a label in this file.")
        print("If you truly have it, it may be spelled differently; check the printed value_counts above.")
    else:
        print(f"Detected '{args.none_label}' label ✅")

    label2id = {l: i for i, l in enumerate(labels)}
    df["y_id"] = df["human_lens"].map(label2id).astype(int)

    # Put embeddings into a consistent column type (store as np.ndarray for easy rebuild after splits)
    df[args.emb_col] = df[args.emb_col].apply(_to_vec)
    if df[args.emb_col].isna().any():
        bad = df[df[args.emb_col].isna()][["poem_id", "beyt_id", "human_lens"]].head(10)
        raise RuntimeError(f"Some embeddings could not be parsed. Examples:\n{bad}")

    # Build full X, y (used only for identifying rare classes; splits will rebuild X from df)
    X_full = np.vstack(df[args.emb_col].to_list())
    y_full = df["y_id"].to_numpy()

    # Robust split
    (df_tr, y_tr), (df_va, y_va), (df_te, y_te) = split_robust(
        df=df,
        X=X_full,
        y=y_full,
        test_size=args.test_size,
        val_size=args.val_size,
        seed=args.seed,
        min_count_for_strat=args.min_count_for_strat,
    )

    # Rebuild X per split from df_* (safe even after moving rows)
    X_tr = np.vstack(df_tr[args.emb_col].to_list())
    X_va = np.vstack(df_va[args.emb_col].to_list())
    X_te = np.vstack(df_te[args.emb_col].to_list())

    class_weight = None if args.class_weight == "none" else "balanced"

    clf = LogisticRegression(
        solver="lbfgs",
        max_iter=5000,
        class_weight=class_weight,
        random_state=args.seed,
    )
    clf.fit(X_tr, y_tr)

    # IMPORTANT: align logits columns to clf.classes_
    # If a class somehow didn't appear in training, clf.classes_ would be a subset.
    # We'll remap y_* into column indices based on clf.classes_.
    classes = clf.classes_
    class_to_col = {int(c): i for i, c in enumerate(classes)}

    def remap_y(y: np.ndarray) -> np.ndarray:
        missing = [int(v) for v in np.unique(y) if int(v) not in class_to_col]
        if missing:
            raise RuntimeError(
                "Some classes exist in val/test but are missing in training. "
                f"Missing class ids: {missing}. Increase labels for those classes or set --min_count_for_strat higher."
            )
        return np.array([class_to_col[int(v)] for v in y], dtype=int)

    # Calibration on val
    logits_va = clf.decision_function(X_va)
    y_va_col = remap_y(y_va)
    ts = TemperatureScaler().fit(logits_va, y_va_col)

    # Evaluate on test
    logits_te = clf.decision_function(X_te)
    probs_te = softmax(logits_te)
    probs_te_cal = ts.proba(logits_te)

    y_te_col = remap_y(y_te)

    yhat_te = probs_te.argmax(axis=1)
    yhat_te_cal = probs_te_cal.argmax(axis=1)

    n_classes = logits_te.shape[1]  # should equal len(labels) if all present in train
    # For confusion matrices, we want order by labels list (0..len(labels)-1),
    # but our probabilities are in clf.classes_ order. We'll build confusion on column indices.
    cm_uncal = confusion_matrix(y_te_col, yhat_te, labels=np.arange(n_classes))
    cm_cal = confusion_matrix(y_te_col, yhat_te_cal, labels=np.arange(n_classes))

    metrics = {
        "n_total": int(len(df)),
        "n_train": int(len(df_tr)),
        "n_val": int(len(df_va)),
        "n_test": int(len(df_te)),
        "labels_original": labels,
        "labels_model_classes": [labels[int(c)] for c in classes],  # class names in model column order
        "class_weight": args.class_weight,
        "temperature_T": float(ts.T),
        "test_top1": topk_acc(probs_te, y_te_col, 1),
        "test_top2": topk_acc(probs_te, y_te_col, 2),
        "test_logloss": float(log_loss(y_te_col, probs_te, labels=np.arange(n_classes))),
        "test_brier": multiclass_brier(probs_te, y_te_col, n_classes),
        "test_ece": ece(probs_te, y_te_col),
        "test_top1_cal": topk_acc(probs_te_cal, y_te_col, 1),
        "test_top2_cal": topk_acc(probs_te_cal, y_te_col, 2),
        "test_logloss_cal": float(log_loss(y_te_col, probs_te_cal, labels=np.arange(n_classes))),
        "test_brier_cal": multiclass_brier(probs_te_cal, y_te_col, n_classes),
        "test_ece_cal": ece(probs_te_cal, y_te_col),
    }

    # Save model bundle
    out_model = Path(args.out_model)
    out_model.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "model": clf,
        "temp_scaler": ts,
        "labels": labels,                # id -> name (global encoding used for y_id)
        "label2id": label2id,            # name -> id
        "model_classes": classes,        # ids present in the trained model (order of logits columns)
        "emb_col": args.emb_col,
        "none_label": args.none_label,
        "seed": args.seed,
        "metrics": metrics,
        "splits": {
            "train_ids": df_tr[["poem_id", "beyt_id"]].to_dict("records"),
            "val_ids": df_va[["poem_id", "beyt_id"]].to_dict("records"),
            "test_ids": df_te[["poem_id", "beyt_id"]].to_dict("records"),
        },
    }
    joblib.dump(bundle, out_model)

    # Report
    out_report = Path(args.out_report)
    out_report.parent.mkdir(parents=True, exist_ok=True)

    model_label_names = [labels[int(c)] for c in classes]

    def cm_to_md(cm: np.ndarray) -> str:
        header = "| true\\pred | " + " | ".join(model_label_names) + " |\n"
        sep = "|" + ("---|" * (len(model_label_names) + 1)) + "\n"
        rows = []
        for i, lab in enumerate(model_label_names):
            rows.append("| " + lab + " | " + " | ".join(str(int(x)) for x in cm[i]) + " |")
        return header + sep + "\n".join(rows) + "\n"

    report = []
    report.append("# Softmax training report\n\n")
    report.append(f"- Labeled file: `{args.labeled_path}`\n")
    report.append(f"- Embeddings file: `{args.embeddings_path}`\n")
    report.append(f"- Total labeled used: **{metrics['n_total']}**\n")
    report.append(f"- Split: train **{metrics['n_train']}**, val **{metrics['n_val']}**, test **{metrics['n_test']}**\n")
    report.append(f"- Classes in model (column order): **{len(model_label_names)}**\n")
    report.append(f"- Model classes: {model_label_names}\n")
    report.append(f"- Temperature T: **{metrics['temperature_T']:.4f}**\n\n")

    report.append("## Test metrics (uncalibrated)\n")
    report.append(f"- Top-1: **{metrics['test_top1']:.4f}**\n")
    report.append(f"- Top-2: **{metrics['test_top2']:.4f}**\n")
    report.append(f"- LogLoss: **{metrics['test_logloss']:.4f}**\n")
    report.append(f"- Brier: **{metrics['test_brier']:.4f}**\n")
    report.append(f"- ECE: **{metrics['test_ece']:.4f}**\n\n")

    report.append("## Test metrics (temperature-calibrated)\n")
    report.append(f"- Top-1: **{metrics['test_top1_cal']:.4f}**\n")
    report.append(f"- Top-2: **{metrics['test_top2_cal']:.4f}**\n")
    report.append(f"- LogLoss: **{metrics['test_logloss_cal']:.4f}**\n")
    report.append(f"- Brier: **{metrics['test_brier_cal']:.4f}**\n")
    report.append(f"- ECE: **{metrics['test_ece_cal']:.4f}**\n\n")

    report.append("## Confusion matrix (uncalibrated)\n")
    report.append(cm_to_md(cm_uncal))
    report.append("\n## Confusion matrix (calibrated)\n")
    report.append(cm_to_md(cm_cal))

    out_report.write_text("".join(report), encoding="utf-8")

    print(f"Saved model: {out_model}")
    print(f"Saved report: {out_report}")


if __name__ == "__main__":
    main()
