# Chunking — Concepts & Interview Notes

> Reference notes for the Insurance Denial Appeal RAG project.
> Covers chunking concepts, production realities, and interview Q&A.

## What chunking is

Chunking = splitting documents into pieces small enough to retrieve precisely
and fit in an LLM's context window, but large enough to carry complete meaning.

The core tension:
- **Too small** → loses context (e.g. "this exclusion shall not apply" — which exclusion?)
- **Too large** → fails for TWO reasons:
  1. May not fit the LLM context window.
  2. Embedding becomes a blurry average of many topics → matches queries poorly.
     (This retrieval-quality reason matters even when size isn't a problem.)

## Overlap

Consecutive chunks share ~10–20% of text at their edges, so an idea spanning a
boundary survives intact in at least one chunk. Costs some redundancy; mitigates
but doesn't fully eliminate the boundary problem.

## Recursive splitting

Split on the most natural boundary available (paragraph), fall back to finer
boundaries (sentence) only when needed — instead of blindly cutting every N chars.
Keeps chunks readable and meaning intact. The standard sensible default.

## Per-document-type strategy (this project)

Inspection of the HICRIC corpus revealed three very different profiles:
- **legal** — huge, dense (avg ~442k chars, max ~39M), no Markdown structure → recursive, section-aware.
- **clinical-guidelines** — shorter (avg ~14k), many records (~40k), clean Markdown headings → split on headings.
- **regulatory-guidance** — medium (avg ~35k), PDF-extraction artifacts (merged words) → recursive after cleaning.

Approach: start with ONE recursive splitter for all three (make it work end-to-end),
then specialize legal/clinical ONLY if Day-5 evaluation shows a category underperforms.
Build simple first; specialize where measurement justifies it.

## How industry approaches chunking

Chunking is empirical and iterative, not a looked-up recipe. Typical progression:
1. Fixed-size chunking (baseline, trivial).
2. Recursive / structural chunking (the workhorse; ~512 tokens, 10–15% overlap as a START point).
3. Document-structure-aware (Markdown/HTML/PDF layout, legal sections).
4. Semantic chunking (split where meaning shifts — expensive, often not worth it).
5. Metadata-enriched (attach source/section/date for filtering + citations).

## Real production problems

- **Tables & lists destroyed** by naive splitters — most common complaint; parsing matters before chunking.
- **Precision vs context** surfaces as bad answers → pattern: small-to-big / parent-document retrieval
  (retrieve on small chunks, feed LLM the larger parent section).
- **Boundaries split critical info** — overlap mitigates, doesn't eliminate.
- **Re-chunking is expensive** — changing strategy means re-embedding everything.
- **Evaluation is the hard part**, not the splitting.

## Late chunking

- **Naive**: split first, embed each chunk independently → chunk has no awareness of rest of document.
- **Late**: embed the WHOLE document first (long-context embedder) so every token is contextualized,
  THEN pool token representations into chunk embeddings → chunks retain document-level context.
- Constraint is the EMBEDDING MODEL'S CONTEXT WINDOW, not database size.
  Works for docs that fit the embedder; for very large docs (e.g. multi-million-char legal texts)
  pre-split into large sections first.
- For this project: documented future improvement, gated by evaluation.

## Interview Q&A

**Q: Walk me through how you'd chunk documents.**
Describe a PROCESS, not a setting. Inspect corpus → start with recursive splitter
(~500 tokens, 10–15% overlap) → tune against retrieval eval. Reference HICRIC inspection
finding three different profiles → single approach not optimal. Let measurement decide specialization.

**Q: How do you decide chunk size?**
No universal size; tradeoff tuned empirically. Too small loses context; too large fails on
context window AND embedding dilution (mention BOTH). Start ~500 tokens, adjust on metrics.

**Q: Purpose of overlap / how much?**
Protects boundary-spanning ideas. 10–20% of chunk size. Mitigates not eliminates →
escalate to parent-document retrieval.

**Q: Small chunk lacks context but big chunk retrieves poorly — solution?**
Small-to-big / parent-document retrieval: retrieve on small chunks (precise),
feed LLM the larger parent section (context).

**Q: Problems you've hit with chunking?**
Tables/lists destroyed; PDF-extraction artifacts. PERSONAL EXAMPLE: HICRIC regulatory-guidance
had merged words from PDF extraction → built a cleaning step before chunking.
Chunking quality is downstream of parsing/cleaning quality.

**Q: Naive vs late chunking?**
Naive = split then embed (no doc context). Late = embed whole doc then pool into chunks
(retains context). Constraint = embedding context window, not DB size.

**Q: How evaluate chunking quality?**
Retrieval eval set; context precision/recall, hit rate; measure PER document type to know
where to specialize. Chunking is measured, not assumed.

**Q: Challenge of changing chunking after deploy?**
Re-embedding everything — expensive, slow. Get it reasonably right early via eval;
treat changes as deliberate tested migrations.

**Lead-with framing:** "Chunking quality is measured against retrieval metrics, not assumed,
and the strategy is chosen per document type based on evaluation — start simple, specialize
only where data shows you need to."

---

## TODO (update after Day 5)
Replace "would expect" / "the plan is" with REAL evaluation numbers once retrieval eval is run.