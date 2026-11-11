import CryptoKit
import Darwin
import Foundation
import FindletCore

// App-less production services and authored scratch data only. No document/query output.
private struct CheckFailure: Error { let code: String }
private func require(_ condition: Bool, _ code: String) throws {
    if !condition { throw CheckFailure(code: code) }
}
private func hash(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}
private func readPrivate(_ url: URL, maximum: Int = 4 * 1_024 * 1_024) throws -> Data {
    let fd = Darwin.open(url.path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC)
    try require(fd >= 0, "private_read_open")
    let handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
    defer { try? handle.close() }
    var before = stat(), after = stat()
    try require(fstat(fd, &before) == 0 && before.st_mode & mode_t(S_IFMT) == mode_t(S_IFREG)
                && before.st_uid == getuid() && before.st_mode & 0o777 == 0o600
                && before.st_size >= 0 && before.st_size <= Int64(maximum), "private_read_identity")
    let data = try handle.read(upToCount: maximum + 1) ?? Data()
    try require(fstat(fd, &after) == 0 && before.st_dev == after.st_dev && before.st_ino == after.st_ino
                && before.st_size == after.st_size && before.st_mtimespec.tv_sec == after.st_mtimespec.tv_sec
                && before.st_mtimespec.tv_nsec == after.st_mtimespec.tv_nsec && Int64(data.count) == before.st_size,
                "private_read_changed")
    return data
}
private func writePrivate(_ data: Data, _ url: URL) throws {
    let fd = Darwin.open(url.path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0o600)
    try require(fd >= 0, "private_write_exclusive")
    let handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
    do { try handle.write(contentsOf: data); try require(fsync(fd) == 0, "private_write_flush"); try handle.close() }
    catch { try? handle.close(); throw error }
}
private struct PointerProof: Codable, Equatable {
    let generation: String
    let pointerSha256: String
    let stateSha256: String
}
private struct QueryProof: Codable {
    let tag: String
    let mode: String
    let expectedPath: String
    let firstPath: String
    let hitCount: Int
    let ids: [String]
    let scores: [Double]
    let excerptsNonempty: Bool
    let originalsResolve: Bool
}
private struct Report: Codable {
    var schemaVersion = "findlet.semantic-harness.v1"
    var phase: String
    var sourceCommit: String
    var checks: [String] = []
    var queries: [QueryProof] = []
    var pointer: PointerProof?
    var cancelledChild: Int32?
    var completed = false
    var failureCode: String?
    var opaqueErrorSha256: String?
}
private struct Context {
    let root: URL
    let library: URL
    let input: URL
    let runtime: RuntimeConfiguration
    let nonce: String
    init(root path: String, nonce: String) throws {
        let url = URL(fileURLWithPath: path, isDirectory: true)
        try require(path.hasPrefix("/") && url.standardizedFileURL.path == path
                    && url.resolvingSymlinksInPath().path == path, "root_path")
        var info = stat()
        try require(Darwin.lstat(path, &info) == 0 && info.st_mode & mode_t(S_IFMT) == mode_t(S_IFDIR)
                    && info.st_uid == getuid() && info.st_mode & 0o777 == 0o700, "root_identity")
        try require(nonce.count == 32 && nonce.allSatisfy { "0123456789abcdef".contains($0) }
                    && (try readPrivate(url.appendingPathComponent(".owner"), maximum: 32)) == Data(nonce.utf8), "root_marker")
        root = url; library = url.appendingPathComponent("library", isDirectory: true)
        input = url.appendingPathComponent("input", isDirectory: true); self.nonce = nonce
        var config = RuntimeConfiguration()
        config.nodePath = url.appendingPathComponent("runtime/node/bin/node").path
        config.qmdPackagePath = url.appendingPathComponent("runtime/tools/node_modules/@tobilu/qmd").path
        config.embeddingModelPath = url.appendingPathComponent("models/Qwen3-Embedding-0.6B-Q8_0.gguf").path
        config.expansionModelPath = url.appendingPathComponent("models/qmd-query-expansion-1.7B-q4_k_m.gguf").path
        config.rerankerModelPath = url.appendingPathComponent("models/qwen3-reranker-0.6b-q8_0.gguf").path
        runtime = config
    }
    func pointer() throws -> PointerProof {
        let raw = try readPrivate(library.appendingPathComponent("current.json"), maximum: 1024)
        guard let json = try JSONSerialization.jsonObject(with: raw) as? [String: Any],
              let generation = json["generation"] as? String, UUID(uuidString: generation) != nil else {
            throw CheckFailure(code: "current_pointer_shape")
        }
        let state = try readPrivate(library.appendingPathComponent("generations/\(generation.lowercased())/state.json"))
        return PointerProof(generation: generation.lowercased(), pointerSha256: hash(raw), stateSha256: hash(state))
    }
    func ownedNodeChildren() throws -> [Int32] {
        let process = Process(), output = Pipe()
        process.executableURL = URL(fileURLWithPath: "/bin/ps")
        process.arguments = ["-axo", "pid=,ppid=,comm="]
        process.standardInput = FileHandle.nullDevice; process.standardOutput = output; process.standardError = FileHandle.nullDevice
        try process.run(); let bytes = output.fileHandleForReading.readDataToEndOfFile(); process.waitUntilExit()
        try output.fileHandleForReading.close()
        try require(process.terminationReason == .exit && process.terminationStatus == 0 && bytes.count < 1_024 * 1_024, "child_observation")
        return String(decoding: bytes, as: UTF8.self).split(separator: "\n").compactMap { line in
            let fields = line.split(maxSplits: 2, whereSeparator: { $0.isWhitespace })
            guard fields.count == 3, let pid = Int32(fields[0]), Int32(fields[1]) == getpid(), String(fields[2]) == runtime.nodePath else { return nil }
            return pid
        }
    }
}

@MainActor private final class Journey {
    let context: Context
    let engine: FindletEngine
    var report: Report
    let probes = [
        ("orbit", "What keeps a satellite circling the planet?", "doc-a.md"),
        ("bake", "Why does dough rise before baking?", "doc-b.md"),
        ("network", "How can two computers exchange messages over a network?", "doc-c.md"),
    ]
    init(context: Context, phase: String, source: String) {
        self.context = context; engine = FindletEngine(applicationSupport: context.library)
        report = Report(phase: phase, sourceCommit: source)
    }
    func check(_ name: String, _ condition: Bool) throws {
        try require(condition, name); try require(!report.checks.contains(name), "duplicate_check"); report.checks.append(name)
    }
    func query(_ tag: String, _ probe: (String, String, String), _ mode: SearchMode,
               _ config: RuntimeConfiguration) async throws {
        let hits = try await engine.search(probe.1, mode: mode, runtime: config)
        try require(!hits.isEmpty && hits.first?.path == probe.2, "expected_top_document_" + tag)
        try require(Set(hits.map(\.documentID)).count == hits.count && hits.count <= 3
                    && hits.allSatisfy { ["doc-a.md", "doc-b.md", "doc-c.md"].contains($0.path) && $0.score.isFinite && !$0.snippet.isEmpty }, "bounded_real_hits_" + tag)
        for hit in hits {
            let original = try await engine.sourceURL(for: hit)
            try require(original == context.input.appendingPathComponent(hit.path), "original_resolution_" + tag)
        }
        report.queries.append(QueryProof(tag: tag, mode: mode.rawValue, expectedPath: probe.2, firstPath: hits[0].path,
                                        hitCount: hits.count, ids: hits.map { $0.documentID.uuidString.lowercased() },
                                        scores: hits.map(\.score), excerptsNonempty: true, originalsResolve: true))
    }
    func prepare() async throws {
        let bookmark = try context.input.bookmarkData(options: [], includingResourceValuesForKeys: nil, relativeTo: nil)
        let folder = FolderSelection(id: UUID(uuidString: "a2c7455d-30ea-47cf-8c37-913617908a32")!, name: "Authored semantic fixture", bookmark: bookmark)
        let built = try await engine.rebuild(folders: [folder], runtime: context.runtime)
        try check("keywordBaseBuiltWithoutModels", built.documentCount == 3 && !built.embeddingReady)
        let before = try context.pointer()
        do { _ = try await engine.prepareSemantic(runtime: context.runtime); throw CheckFailure(code: "unaccepted_preparation_allowed") }
        catch is FindletError { try check("explicitPreparationConsentRequired", try context.pointer() == before) }
        var config = context.runtime; config.modelPreparationAccepted = true
        let ready = try await engine.prepareSemantic(runtime: config)
        try check("actualEmbeddingPreparationCompleted", ready.documentCount == 3 && ready.embeddingReady)
        let pointer = try context.pointer(); try check("semanticGenerationPublished", pointer.generation != before.generation)
        for (i, probe) in probes.enumerated() {
            try await query("S01Q\(i * 2 + 1)", probe, .semantic, config)
            try await query("S01Q\(i * 2 + 2)", probe, .hybrid, config)
        }
        try check("queriesPreservePublishedPointerAndState", try context.pointer() == pointer)
        report.pointer = pointer
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        try writePrivate(encoder.encode(pointer), context.root.appendingPathComponent("semantic-handoff.json"))
        try check("noNativeChildRemainsAfterQueries", try context.ownedNodeChildren().isEmpty)
    }
    func reopen() async throws {
        let saved = try JSONDecoder().decode(PointerProof.self, from: readPrivate(context.root.appendingPathComponent("semantic-handoff.json")))
        try check("newProcessPreservesPublishedState", try context.pointer() == saved)
        let summary = try await engine.summary()
        try check("newEngineReadsSemanticReadiness", summary.documentCount == 3 && summary.embeddingReady)
        var config = context.runtime; config.modelPreparationAccepted = true
        try await query("S02Q1", probes[0], .hybrid, config)
        var invalid = config; invalid.embeddingModelPath = context.root.appendingPathComponent("negative/invalid.gguf").path
        do { _ = try await engine.prepareSemantic(runtime: invalid); throw CheckFailure(code: "invalid_native_model_accepted") }
        catch is FindletError { try check("failedNativePreparationPreservesState", try context.pointer() == saved) }
        let names = try FileManager.default.contentsOfDirectory(atPath: context.library.appendingPathComponent("generations").path)
        try check("failedStagedGenerationRemoved", names == [saved.generation])
        let pending = Task { try await self.engine.search(self.probes[1].1, mode: .hybrid, runtime: config) }
        var child: Int32?
        for _ in 0..<200 {
            let children = try context.ownedNodeChildren(); try require(children.count <= 1, "unexpected_native_children")
            if let first = children.first { child = first; break }
            try await Task.sleep(nanoseconds: 50_000_000)
        }
        guard let child else { await engine.cancel(); _ = await pending.result; throw CheckFailure(code: "native_child_not_observed") }
        report.cancelledChild = child
        await engine.cancel()
        switch await pending.result {
        case .failure(let error): try check("ownedNativeQueryCancelled", error is CancellationError)
        case .success: throw CheckFailure(code: "cancelled_query_reported_success")
        }
        try check("cancelledNativeChildExited", try !context.ownedNodeChildren().contains(child))
        try check("cancellationPreservesSemanticState", try context.pointer() == saved)
        try await query("S02Q2", probes[1], .semantic, config)
        try await engine.forgetIndex()
        let empty = try await engine.summary()
        try check("forgetClearsSemanticSummary", empty.documentCount == 0 && !empty.embeddingReady)
        try check("forgetRemovesPointer", !FileManager.default.fileExists(atPath: context.library.appendingPathComponent("current.json").path))
        for name in ["generations", "cache"] {
            try check("forgetEmpties_" + name, try FileManager.default.contentsOfDirectory(atPath: context.library.appendingPathComponent(name).path).isEmpty)
        }
        try check("noNativeChildRemainsAfterForget", try context.ownedNodeChildren().isEmpty)
    }
    func run() async -> Report {
        do {
            if report.phase == "prepare" { try await prepare() }
            else if report.phase == "reopen" { try await reopen() }
            else { throw CheckFailure(code: "unknown_phase") }
            report.completed = true
        } catch let error as CheckFailure { report.failureCode = error.code }
        catch { report.failureCode = error is CancellationError ? "unexpected_cancellation" : "production_or_harness_failure"; report.opaqueErrorSha256 = hash(Data(error.localizedDescription.utf8)) }
        await engine.cancel()
        return report
    }
}

@main private struct SemanticPipelineMain {
    @MainActor static func main() async {
        let args = Array(CommandLine.arguments.dropFirst())
        var report = Report(phase: args.first ?? "unknown", sourceCommit: "unbound")
        do {
            try require(args.count == 4 && ["prepare", "reopen"].contains(args[0]) && args[3].count == 40
                        && args[3].allSatisfy { "0123456789abcdef".contains($0) }, "launch_shape")
            let context = try Context(root: args[1], nonce: args[2])
            report = await Journey(context: context, phase: args[0], source: args[3]).run()
        } catch let error as CheckFailure { report.failureCode = error.code }
        catch { report.failureCode = "launch_failed"; report.opaqueErrorSha256 = hash(Data(error.localizedDescription.utf8)) }
        do {
            let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
            var bytes = try encoder.encode(report); bytes.append(0x0a)
            try require(bytes.count <= 128 * 1024, "report_bound")
            try FileHandle.standardOutput.write(contentsOf: bytes)
        } catch { Darwin.exit(2) }
        Darwin.exit(report.completed ? 0 : 1)
    }
}
