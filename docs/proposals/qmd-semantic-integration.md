# Actual local-model semantic and hybrid pipeline

Findlet's [owning contract](../specs/local-search.md) includes explicit model
preparation, expanded semantic search and hybrid/reranked retrieval. Keyword
K01/K02 and the downloadable preview are already accepted and remain closed.
This separate scope exercises the existing production services with real local
inference. Standing owner approval to do all project work applies; no new paid
provider/account or access to personal files is proposed.

S01 compiles an app-less harness against the unchanged two core/four service
files, creates three tiny authored topic documents in owned scratch and rebuilds
the index. Preparation without its explicit consent flag must fail without
changing the current pointer/state. Real preparation using the three pinned
models must publish complete embeddings. Three authored conceptual probes each
exercise actual Semantic/vsearch and Hybrid/query; the expected document must
rank first, all scores/excerpts/IDs must be valid and original resolution exact.
This is a small authored retrieval check, not a general quality benchmark.

S02 starts a new process, reopens the same semantic index, searches again and
requires a deliberately invalid native GGUF preparation to preserve the previous
complete generation. It observes an actual direct-child Node query before calling
the production cancellation API, verifies cancellation/child exit and successful
later retrieval, then Forgets generated data while originals/runtime/models stay
unchanged. No fake model outputs or replacement process/engine is used.

Use [pinned model metadata](../../Tests/fixtures/qmd-semantic-models.json): official
Qwen embedding0.6B Q8 and ggml-org Qwen reranker0.6B Q8 under Apache2 metadata,
plus QMD expansion1.7B Q4 under MIT metadata. The exact ungated revisions/LFS
hashes total2,560,742,688bytes. They are downloaded only to temporary CI scratch,
verified by size/full SHA256/GGUF header and removed afterward. No weights,
vectors, model/index cache, bookmarks, document text or queries enter evidence
or the app archive. The Qwen embedding alternative is supported by pinned
[QMD2.8.3](https://github.com/tobi/qmd/blob/86d2365d17fc682e491c2c53d1e4a884aee8682a/src/llm.ts).

The semantic test lock derives from the existing Darwin lock: all179 dependency
paths and version/resolved/integrity values stay exact. Only the already-pinned
mac-arm64-metal3.20 package becomes an explicit test dependency. Node26.13.0
retains its verified official archive hash. No install script, optional other
platform, source compilation fallback or implicit model setup is allowed.
QMD_FORCE_CPU is the actual production setting; native admission must establish
offloading=false. Apple Silicon may load the packaged Metal backend with model
gpuLayers0 as supported by QMD. This is not a CPU-only binary claim.

One public macOS15 ARM64/Xcode16.4 job is capped20minutes, with bounded work,
cleanup reserve, every child/stream, downloads and6GiB scratch. Preserve HOME,
use task-owned config/cache/temp and exact source exports, and refuse unowned
or pre-existing work. Capture full bounded outer streams and independent closed
index/vector metadata checks; production QMD stderr stays internally discarded
and is not claimed as retained evidence. Source/runtime/model/original hashes,
owned processes and scratch must be checked before teardown. Failures stay
failed; later phases stay unrun after a failed prerequisite.

No app UI, shortcut/permission flow, private corpus, store signing, provider API,
paid plan or local heavy execution is part of this scope. Strict network-offline
and general semantic-quality claims remain separate. Local Storage Guard fails
at0.8GiB free/38required, so no local models, install, compile or execution.
