# Third-party runtime

Findlet does not bundle QMD, Node, native inference bindings or GGUF model files. No QMD implementation source was copied. Its external CLI contract was reviewed at [tobi/qmd 86d2365d](https://github.com/tobi/qmd/commit/86d2365d17fc682e491c2c53d1e4a884aee8682a), package version 2.8.3. QMD is [MIT-licensed](https://github.com/tobi/qmd/blob/86d2365d17fc682e491c2c53d1e4a884aee8682a/LICENSE); Node and native dependencies have their own notices.

Model licensing is separate from the app and QMD. The user supplies compatible, legally obtained local assets. The QMD defaults documented at that commit include [EmbeddingGemma](https://huggingface.co/google/embeddinggemma-300m), [Qwen3 Reranker GGUF](https://huggingface.co/ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF), and [QMD query-expansion GGUF](https://huggingface.co/tobil/qmd-query-expansion-1.7B-gguf). No model-license acceptance, download or redistribution has been performed by this project.

The app checks package name/version metadata and the selected compiled entry, not the authenticity of every installed dependency. Select a trusted installation. An exact runtime/asset/license manifest is required before any bundled redistribution.
