# Data Card — Insurance Denial Appeal RAG

This document records the **provenance, scope, schema, quality, and licensing** of the
knowledge base used by this project. It is the single source of truth for *why* the corpus
looks the way it does. If you change what data the system ingests, update this file in the
same commit.

---

## 1. Overview

The retrieval knowledge base (KB) is built from **HICRIC** — a corpus of U.S. health-insurance
regulatory, legal, and clinical text. The RAG system retrieves grounded provisions from this
corpus to generate citation-backed insurance denial appeal letters.

This card documents a **deliberate subset** of HICRIC, not the whole dataset. The scoping
decisions and their reasons are in Section 4.

---

## 2. Source & provenance

| Field | Value |
|---|---|
| Dataset | HICRIC |
| Host | Hugging Face Datasets |
| Repo | `Persius/hicric` |
| Access pattern | `load_dataset('Persius/hicric', '<config>')` per category |
| Pinned revision | `e9304975feff9ccaaf15cf547f698590d00d78c3y` |
| Local cache | `data/raw/hicric/` |

**Revision pinning.** The download script pins a specific dataset revision rather than pulling
"latest." This makes the corpus reproducible: a teammate (or future you) who reruns ingestion
gets byte-identical data. The authoritative pin lives in `src/ingestion/download.py`; the hash
above must match it.

> Note: a previously considered dataset, "CIMRD," **does not exist** (it was confabulated during
> early planning) and a synthetic-claims dataset was also dropped. The KB is **HICRIC only**.

---

## 3. License & attribution

| Asset | License |
|---|---|
| HICRIC data | CC-BY-SA 4.0 |
| This project's code | Apache 2.0 |

**Attribution requirement.** Because the data is CC-BY-SA 4.0, any use must credit the source
and share derivative data under the same license. Attribute as:

> "HICRIC Data" — https://huggingface.co/datasets/Persius/hicric

Generated appeal letters are derived *content*, not redistributed data, but the corpus and any
processed/exported version of it carry the CC-BY-SA 4.0 obligation.

---

## 4. Scope decision — what's in the KB and what isn't

HICRIC ships as **6 configs**. We deliberately use **3** as the knowledge base, hold **1** for
future evaluation, and **exclude 2**. The reasoning matters more than the list.

### Included in the KB (3 configs)

| Config | Records | Why included |
|---|---|---|
| `regulatory-guidance` | 1,110 | Authoritative rules insurers must follow — core to appeals |
| `legal` | 1,348 | Statutes / legal provisions — strongest citation authority |
| `clinical-guidelines` | 40,110 | Medical-necessity standards — counters clinical denials |

### Held for evaluation, NOT in the KB

| Config | Role |
|---|---|
| `case-description` | Real denials with **outcome fields**. This becomes the basis of the Day‑5 golden evaluation set — feeding it into the KB would leak answers into retrieval. Kept strictly separate. |

### Excluded entirely

| Config | Why excluded |
|---|---|
| `contract-coverage-rule-medical-policy` | 1.3 GB across 7 files. On an 8 GB M1, the ingest/clean/chunk cost is not justified by marginal citation value for an MVP. Documented as a production-scale trigger. |
| `opinion-policy-summary` | Non-definitive / opinion-grade text. Weak citation authority for a system whose entire promise is *grounded, authoritative* appeals. |

**Trigger to revisit:** if Day‑5 eval shows appeals failing for lack of contract/coverage-rule
grounding, ingest `contract-coverage-rule-medical-policy` (streaming, given its size).

---

## 5. Record schema

Each record (across all configs) carries these fields:

| Field | Description | Use in this project |
|---|---|---|
| `text` | The document body | Cleaned → chunked → embedded |
| `tags` | Category / authority labels; most KB records carry a `kb` authority tag | Metadata + scope filtering |
| `date_accessed` | When the source was captured | Provenance |
| `source_url` | Real, populated URL of the original source | **Powers citations in the appeal letter** |
| `source_md5` | Checksum of the source | Provenance / dedup |
| `relative_path` | Path within the source corpus | Provenance + chunk metadata |

`source_url` being real and populated is the reason this corpus is viable for a *citation-first*
system — every chunk can point back to a verifiable origin.

---

## 6. Corpus statistics & a key finding

### Length profiles (differ wildly by category)

| Category | Records | Avg length | Notes |
|---|---|---|---|
| `legal` | 1,348 | ~442k chars | Extreme outliers; **max ~39M chars** in a single record |
| `clinical-guidelines` | 40,110 | ~14k chars | Many records, moderate length |
| `regulatory-guidance` | 1,110 | ~35k chars | Moderate |

**Engineering consequence:** the legal max (~39M chars) means cleaning and chunking **must
stream** — process one record, emit its chunks, release it — never hold the corpus (or even one
huge record's full derived state) in memory at once. This is a hard constraint on an 8 GB machine.

### "documents" ≠ "records"

The repo's headline stats count **documents**, but `load_dataset` returns **records**, and a
single document is split into many records. Record counts above are what actually downloads —
do not expect them to match the repo's document figures.

---

## 7. Data quality & known limitations

Cleaning needs differ by category. We do **minimal, safe** cleaning and explicitly document what
we leave alone, rather than gold-plating.

| Category | Quality issue | Our action |
|---|---|---|
| `regulatory-guidance` | **Merged words** (`deniedclaim`) from crude PDF text extraction | **Not repaired now** — see ladder below |
| `legal` | Header/footer cruft, but text is readable | Strip obvious repeated cruft; collapse whitespace |
| `clinical-guidelines` | Clean, **with Markdown headings** | Keep headings — they can populate the `section` citation field |
| *all* | Near-empty junk records (1–3 chars) | **Filter out** below a minimum-length threshold |

### Known limitation: merged words (regulatory category)

Merged words are an **extraction artifact**, not a content problem. PDFs store glyphs at
coordinates, not words; when an extractor fails to infer the gap between glyphs, adjacent words
fuse. HICRIC's text was already extracted (badly, for this category) upstream, and we **do not
have the source PDFs**, so the cleanest fixes (choosing a better extractor / OCR / Document-AI
service) are unavailable to us.

The remaining option — dictionary/n-gram **word-segmentation** (e.g. `wordsegment`) — *guesses*
split points. It handles plain English acceptably but **mangles legal jargon and statute
citations**, so applying it blindly across the corpus risks making retrieval *worse*.

**Why deferring is the correct call, not laziness:**
- The system is **hybrid retrieval**. The **dense** side (BGE/E5, sub-word tokenizers) is largely
  robust to merged words. Only the **BM25** (exact-token) side loses recall on fused tokens. The
  damage is therefore *partial* and *unmeasured*.
- Fixing before measuring is exactly the over-engineering this project avoids.

**Trigger + planned fix:** if **Day‑5 eval** shows BM25 recall degrading on `regulatory-guidance`
chunks, apply **targeted** `wordsegment` to only the flagged spans, protected by a domain-term
whitelist (statutes, USC/CFR citations, proper nouns) — never a blind whole-corpus pass.

---

## 8. Jurisdiction boundary

HICRIC is **U.S.-jurisdiction** health-insurance text. The target job markets for this portfolio
are **India and Dubai (BFSI)**. This is a known, documented boundary:

- The *architecture* (extraction → hybrid retrieval → rerank → grounded, cited generation →
  guardrails → eval) is jurisdiction-agnostic and transfers directly.
- The *corpus* is not. Adapting to India/Dubai requires swapping in IRDAI / DHA / relevant
  regulatory and clinical sources. That is a **data-layer change, not an architecture change** —
  which is itself the point the project demonstrates.

---

## 9. Versioning policy

- The dataset is **static** for this project, so DVC is intentionally not used (trigger: a dynamic
  / growing corpus).
- Reproducibility comes from the **pinned HICRIC revision** (Section 2) plus a config-driven,
  versioned eval harness (Day 5+).
- Any change to scope, cleaning, or chunking that alters the processed corpus must bump a note
  here and be committed alongside the code change.

---

*Last updated: Day 2. Maintainer: project owner.*
