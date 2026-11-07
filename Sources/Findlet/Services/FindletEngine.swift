import CryptoKit
import Darwin
import Foundation
import FindletCore

actor FindletEngine {
    private struct Current: Codable { let version: Int; let generation: UUID }
    private struct GenerationOwner: Codable { let version: Int; let app: String; let generation: UUID }
    private struct State: Codable {
        var manifest: IndexManifest
        let runtimeStamp: String
        var modelStamp: String?
    }
    private struct Runtime {
        let node: URL
        let entry: URL
        let sdk: URL
        let stamp: String
    }
    private struct IndexHealth: Decodable {
        struct Collection: Decodable { let name: String; let path: String; let pattern: String; let documents: Int }
        let totalDocuments: Int
        let needsEmbedding: Int
        let hasVectorIndex: Bool
        let collections: [Collection]
    }
    private struct IndexedRow: Decodable {
        let collection: String
        let path: String
        let content_present: Int
    }
    private struct Models {
        let values: [String: String]
        let stamp: String
    }
    private struct ClosedAuditFile {
        let info: stat
        let sha256: String
        let prefix: Data
    }
    private struct ClosedAuditSidecar {
        let name: String
        let file: ClosedAuditFile?
    }
    private struct ClosedAuditSnapshot {
        let rootInfo: stat
        let generationsInfo: stat
        let generationInfo: stat
        let lock: ClosedAuditFile
        let owner: ClosedAuditFile
        let database: ClosedAuditFile
        let sidecars: [ClosedAuditSidecar]
    }
    private let root: URL
    private let gate = OperationGate()
    private let runner = QMDProcessRunner()
    private var epoch = 0
    private let manager = FileManager.default
    private var lockDescriptor: Int32 = -1

    init(applicationSupport: URL) { root = applicationSupport.standardizedFileURL }
    deinit { if lockDescriptor >= 0 { _ = Darwin.close(lockDescriptor) } }

    func summary() throws -> IndexSummary {
        try ensureDirectories()
        guard let state = try loadState() else { return IndexSummary() }
        return describe(state)
    }

    func rebuild(folders: [FolderSelection], runtime configuration: RuntimeConfiguration) async throws -> IndexSummary {
        try await gate.enter()
        defer { Task { await gate.leave() } }
        try Task.checkCancellation()
        try ensureDirectories()
        // Preserve a corrupt/unreadable current generation until explicit Forget Index.
        _ = try loadState()
        let runtime = try validateRuntime(configuration)
        let operationEpoch = epoch
        let directory = try newGeneration()
        var committed = false
        defer { if !committed { try? manager.removeItem(at: directory) } }
        let manifest = try CorpusBuilder.build(folders: folders, at: directory)
        try check(operationEpoch)
        try configure(directory, models: nil)
        _ = try await invoke(runtime, in: directory, arguments: ["--index", "findlet", "update"])
        try await verifyIndex(runtime, directory: directory, documents: manifest.documents, semantic: false)
        try check(operationEpoch)
        let state = State(manifest: manifest, runtimeStamp: runtime.stamp, modelStamp: nil)
        try commit(state, directory: directory)
        committed = true
        return describe(state)
    }

    func prepareSemantic(runtime configuration: RuntimeConfiguration) async throws -> IndexSummary {
        try await gate.enter()
        defer { Task { await gate.leave() } }
        try Task.checkCancellation()
        try ensureDirectories()
        guard let old = try loadState() else { throw FindletError.message("Build a keyword index first.") }
        let runtime = try validateRuntime(configuration)
        guard runtime.stamp == old.runtimeStamp else { throw FindletError.message("The runtime changed. Rebuild the index first.") }
        let models = try validateModels(configuration)
        let operationEpoch = epoch
        let directory = try newGeneration()
        var committed = false
        defer { if !committed { try? manager.removeItem(at: directory) } }
        let corpus = directory.appendingPathComponent("corpus", isDirectory: true)
        try createPrivateDirectory(corpus)
        let oldDirectory = generationURL(old.manifest.generation)
        for document in old.manifest.documents {
            try check(operationEpoch)
            let source = oldDirectory.appendingPathComponent("corpus").appendingPathComponent(document.snapshotName)
            try requireRegular(source)
            let destination = corpus.appendingPathComponent(document.snapshotName)
            try manager.copyItem(at: source, to: destination)
            try manager.setAttributes([.posixPermissions: 0o600], ofItemAtPath: destination.path)
        }
        try configure(directory, models: models)
        _ = try await invoke(runtime, in: directory, arguments: ["--index", "findlet", "update"])
        try check(operationEpoch)
        let embedded = try await invoke(runtime, in: directory, arguments: ["--index", "findlet", "embed", "--force", "--timeout", "30", "--max-docs-per-batch", "50", "--max-batch-mb", "64"])
        let completion = String(decoding: embedded, as: UTF8.self)
        guard completion.contains("Done! Embedded"), !completion.contains("chunks still failed after retries"),
              !completion.contains("Another embed process is already running. Skipping.") else {
            throw FindletError.message("QMD did not confirm complete embedding. The previous index is retained.")
        }
        try await verifyIndex(runtime, directory: directory, documents: old.manifest.documents, semantic: true)
        try check(operationEpoch)
        var manifest = IndexManifest(generation: UUID(uuidString: directory.lastPathComponent)!, documents: old.manifest.documents, folders: old.manifest.folders)
        manifest.embeddingReady = true
        let state = State(manifest: manifest, runtimeStamp: runtime.stamp, modelStamp: models.stamp)
        try commit(state, directory: directory)
        committed = true
        return describe(state)
    }

    func search(_ query: String, mode: SearchMode, runtime configuration: RuntimeConfiguration) async throws -> [SearchHit] {
        let arguments = try QMDContract.searchArguments(query: query, mode: mode)
        try await gate.enter()
        defer { Task { await gate.leave() } }
        try Task.checkCancellation()
        try ensureDirectories()
        guard let state = try loadState() else { throw FindletError.message("Choose folders and build an index in Settings.") }
        let runtime = try validateRuntime(configuration)
        guard runtime.stamp == state.runtimeStamp else { throw FindletError.message("The runtime changed. Rebuild the index first.") }
        let models: Models?
        if mode.needsModels {
            let selectedModels = try validateModels(configuration)
            guard state.manifest.embeddingReady, selectedModels.stamp == state.modelStamp else {
                throw FindletError.message("Prepare semantic search for these model files in Settings first.")
            }
            models = selectedModels
        } else { models = nil }
        let operationEpoch = epoch
        let directory = generationURL(state.manifest.generation)
        // Recreate only curated config: never inherit configuration written by another tool.
        try configure(directory, models: models)
        let data = try await invoke(runtime, in: directory, arguments: arguments)
        try check(operationEpoch)
        return try QMDContract.decodeResults(data, manifest: state.manifest, generationURL: directory)
    }

    func sourceURL(for hit: SearchHit) throws -> URL {
        guard let state = try loadState(), let document = state.manifest.documents.first(where: { $0.id == hit.documentID }) else {
            throw FindletError.message("This result is no longer part of the current index.")
        }
        return try CorpusBuilder.sourceURL(for: document, in: state.manifest)
    }

    func cancel() async { epoch += 1; await runner.cancel() }

    func forgetIndex() async throws {
        try await gate.enter()
        defer { Task { await gate.leave() } }
        try Task.checkCancellation()
        try ensureDirectories()
        // Validate ownership before deletion; never follow an unexpected symlink.
        let directories = try manager.contentsOfDirectory(at: generations, includingPropertiesForKeys: [.isSymbolicLinkKey])
        for directory in directories {
            guard UUID(uuidString: directory.lastPathComponent) != nil else {
                throw FindletError.message("An unrecognized item is present in Findlet's index directory. Nothing was removed.")
            }
            try requireDirectory(directory)
            try requireOwnedGeneration(directory)
        }
        let pointer = root.appendingPathComponent("current.json")
        if pathExists(pointer) { try requireRegular(pointer); try manager.removeItem(at: pointer) }
        for directory in directories { try manager.removeItem(at: directory) }
        let cache = root.appendingPathComponent("cache", isDirectory: true)
        try requireDirectory(cache)
        try manager.removeItem(at: cache)
        try createPrivateDirectory(cache)
    }

    private var generations: URL { root.appendingPathComponent("generations", isDirectory: true) }
    private func generationURL(_ id: UUID) -> URL { generations.appendingPathComponent(id.uuidString.lowercased(), isDirectory: true) }

    private func newGeneration() throws -> URL {
        let directory = generationURL(UUID())
        guard !manager.fileExists(atPath: directory.path) else { throw FindletError.message("An index generation already exists.") }
        try createPrivateDirectory(directory)
        let id = UUID(uuidString: directory.lastPathComponent)!
        do { try write(GenerationOwner(version: 1, app: "com.alvarovillalbaa.Findlet", generation: id), to: directory.appendingPathComponent("owner.json")) }
        catch { try? manager.removeItem(at: directory); throw error }
        return directory
    }

    private func ensureDirectories() throws {
        try createPrivateDirectory(root)
        if lockDescriptor < 0 {
            let file = root.appendingPathComponent("engine.lock")
            let descriptor = Darwin.open(file.path, O_RDWR | O_CREAT | O_NOFOLLOW | O_CLOEXEC, 0o600)
            guard descriptor >= 0 else { throw FindletError.message("Findlet's operation lock could not be opened.") }
            guard flock(descriptor, LOCK_EX | LOCK_NB) == 0 else {
                _ = Darwin.close(descriptor)
                throw FindletError.message("Another Findlet instance is using this library. Close it first.")
            }
            lockDescriptor = descriptor
        }
        try createPrivateDirectory(generations)
        try createPrivateDirectory(root.appendingPathComponent("cache", isDirectory: true))
    }

    private func createPrivateDirectory(_ directory: URL) throws {
        if manager.fileExists(atPath: directory.path) { try requireDirectory(directory) }
        else { try manager.createDirectory(at: directory, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700]) }
        try manager.setAttributes([.posixPermissions: 0o700], ofItemAtPath: directory.path)
    }

    private func requireDirectory(_ directory: URL) throws {
        let values = try directory.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])
        guard values.isDirectory == true, values.isSymbolicLink != true else { throw FindletError.message("An index directory is missing or is a symbolic link.") }
    }

    private func requireRegular(_ file: URL) throws {
        let values = try file.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
        guard values.isRegularFile == true, values.isSymbolicLink != true else { throw FindletError.message("An index file is missing or is a symbolic link.") }
    }

    private func pathExists(_ file: URL) -> Bool {
        var info = stat()
        return Darwin.lstat(file.path, &info) == 0
    }

    private func requireOwnedGeneration(_ directory: URL) throws {
        let owner = try JSONDecoder().decode(GenerationOwner.self, from: read(directory.appendingPathComponent("owner.json"), limit: 1_024))
        guard owner.version == 1, owner.app == "com.alvarovillalbaa.Findlet",
              owner.generation == UUID(uuidString: directory.lastPathComponent) else {
            throw FindletError.message("An index directory has no valid Findlet ownership marker. It was left unchanged.")
        }
    }

    private func read(_ file: URL, limit: Int = 4 * 1_024 * 1_024) throws -> Data {
        try requireRegular(file)
        let handle = try FileHandle(forReadingFrom: file)
        defer { try? handle.close() }
        let data = try handle.read(upToCount: limit + 1) ?? Data()
        guard data.count <= limit else { throw FindletError.message("An index or runtime metadata file exceeds its limit.") }
        return data
    }

    private func write<T: Encodable>(_ value: T, to file: URL) throws {
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        try writePrivate(encoder.encode(value), to: file)
    }

    private func writePrivate(_ data: Data, to file: URL) throws {
        if pathExists(file) { try requireRegular(file) }
        let temporary = file.deletingLastPathComponent().appendingPathComponent(".write-" + UUID().uuidString)
        let descriptor = Darwin.open(temporary.path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0o600)
        guard descriptor >= 0 else { throw FindletError.message("Private index metadata could not be created.") }
        defer { _ = Darwin.unlink(temporary.path) }
        let handle = FileHandle(fileDescriptor: descriptor, closeOnDealloc: true)
        do {
            try handle.write(contentsOf: data)
            guard fsync(descriptor) == 0 else { throw FindletError.message("Index metadata could not be flushed.") }
            try handle.close()
        } catch { try? handle.close(); throw error }
        guard Darwin.rename(temporary.path, file.path) == 0 else { throw FindletError.message("Index metadata could not be atomically replaced.") }
        // No fallible action after publishing the pointer: callers must not delete a committed generation.
    }

    private func loadState() throws -> State? {
        let pointer = root.appendingPathComponent("current.json")
        guard pathExists(pointer) else { return nil }
        let current = try JSONDecoder().decode(Current.self, from: read(pointer, limit: 1_024))
        guard current.version == 1 else { throw FindletError.message("This index uses an unsupported version.") }
        let directory = generationURL(current.generation)
        try requireDirectory(directory)
        try requireOwnedGeneration(directory)
        let state = try JSONDecoder().decode(State.self, from: read(directory.appendingPathComponent("state.json")))
        let manifest = state.manifest
        guard manifest.version == 1, manifest.generation == current.generation,
              !manifest.documents.isEmpty, manifest.documents.count <= 2_000,
              Set(manifest.documents.map(\.id)).count == manifest.documents.count,
              Set(manifest.folders.map(\.id)).count == manifest.folders.count,
              manifest.documents.allSatisfy({ document in manifest.folders.contains(where: { $0.id == document.folderID }) }) else {
            throw FindletError.message("The index manifest is invalid. Forget it explicitly before starting over.")
        }
        try requireDirectory(directory.appendingPathComponent("corpus"))
        return state
    }

    private func configure(_ directory: URL, models: Models?) throws {
        let config = directory.appendingPathComponent("config", isDirectory: true)
        try createPrivateDirectory(config)
        var value: [String: Any] = ["collections": [QMDContract.collection: [
            "path": directory.appendingPathComponent("corpus").path,
            "pattern": "**/*.md", "includeByDefault": true,
        ]]]
        if let models { value["models"] = models.values }
        let file = config.appendingPathComponent("findlet.yml")
        // JSON is a YAML subset accepted by QMD; paths never enter shell strings.
        try writePrivate(JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]), to: file)
    }

    private func commit(_ state: State, directory: URL) throws {
        try write(state, to: directory.appendingPathComponent("state.json"))
        try write(Current(version: 1, generation: state.manifest.generation), to: root.appendingPathComponent("current.json"))
        // Keep only the active generation. Originals and configured model/runtime files are outside this tree.
        for old in (try? manager.contentsOfDirectory(at: generations, includingPropertiesForKeys: nil)) ?? [] where old != directory {
            guard UUID(uuidString: old.lastPathComponent) != nil,
                  (try? old.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])).map({ $0.isDirectory == true && $0.isSymbolicLink != true }) == true else { continue }
            guard (try? requireOwnedGeneration(old)) != nil else { continue }
            try? manager.removeItem(at: old)
        }
    }

    private func invoke(_ runtime: Runtime, in directory: URL, arguments: [String]) async throws -> Data {
        try Task.checkCancellation()
        return try await runner.run(executable: runtime.node, arguments: [runtime.entry.path] + arguments,
                                    directory: directory, environment: environment(runtime, directory: directory))
    }

    private func verifyIndex(_ runtime: Runtime, directory: URL, documents: [IndexedDocument], semantic: Bool) async throws {
        try Task.checkCancellation()
        let expectedDocuments = documents.count
        // Fixed SDK program; paths are positional arguments, never source/shell interpolation.
        // createStore/getStatus may initialize/sync this owned DB. They do not run model inference.
        let program = """
        import { pathToFileURL } from 'node:url';
        const { createStore } = await import(pathToFileURL(process.argv[1]).href);
        const store = await createStore({dbPath:process.argv[2],configPath:process.argv[3]});
        try {
          const s = await store.getStatus();
          process.stdout.write(JSON.stringify({totalDocuments:s.totalDocuments,needsEmbedding:s.needsEmbedding,hasVectorIndex:s.hasVectorIndex,
            collections:s.collections.map(c=>({name:c.name,path:c.path,pattern:c.pattern,documents:c.documents}))}));
        } finally { await store.close(); }
        """
        let data = try await runner.run(executable: runtime.node,
            arguments: ["--input-type=module", "--eval", program, runtime.sdk.path,
                        directory.appendingPathComponent("index.sqlite").path,
                        directory.appendingPathComponent("config/findlet.yml").path],
            directory: directory, environment: environment(runtime, directory: directory))
        let health = try JSONDecoder().decode(IndexHealth.self, from: data)
        guard health.totalDocuments == expectedDocuments, health.collections.count == 1,
              let collection = health.collections.first,
              collection.name == QMDContract.collection, collection.documents == expectedDocuments,
              URL(fileURLWithPath: collection.path).standardizedFileURL == directory.appendingPathComponent("corpus").standardizedFileURL,
              collection.pattern == "**/*.md" else {
            throw FindletError.message("QMD did not index the entire selected corpus. The previous index is retained.")
        }
        guard !semantic || (health.hasVectorIndex && health.needsEmbedding == 0) else {
            throw FindletError.message("QMD reports unfinished embeddings. The previous index is retained.")
        }
        // Only normal metadata tables are queried; vanilla SQLite never touches vec0.
        let sql = "SELECT d.collection,d.path,CASE WHEN c.hash IS NULL THEN 0 ELSE 1 END AS content_present FROM documents d LEFT JOIN content c ON c.hash=d.hash WHERE d.active=1 ORDER BY d.collection,d.path;"
        // The SDK process has exited and closed its store. Immutable access is
        // restricted to a stable private generation with no pending sidecars.
        let auditBefore = try closedAuditSnapshot(directory)
        var components = URLComponents()
        components.scheme = "file"
        components.host = ""
        components.path = directory.appendingPathComponent("index.sqlite").path
        components.queryItems = [URLQueryItem(name: "mode", value: "ro"), URLQueryItem(name: "immutable", value: "1")]
        guard let databaseURI = components.string else { throw closedAuditFailure() }
        let rowsData = try await runner.run(executable: URL(fileURLWithPath: "/usr/bin/sqlite3"),
            arguments: ["-init", "/dev/null", "-readonly", "-json", databaseURI, sql],
            directory: directory, environment: environment(runtime, directory: directory))
        let auditAfter = try closedAuditSnapshot(directory)
        guard sameClosedAudit(auditBefore, auditAfter) else { throw closedAuditFailure() }
        let rows = try JSONDecoder().decode([IndexedRow].self, from: rowsData)
        guard rows.count == expectedDocuments, Set(rows.map(\.path)) == Set(documents.map(\.snapshotName)),
              rows.allSatisfy({ $0.collection == QMDContract.collection && $0.content_present == 1 }) else {
            throw FindletError.message("QMD's indexed file list does not match the prepared corpus. The previous index is retained.")
        }
    }

    private func closedAuditFailure() -> FindletError {
        .message("The completed QMD index is not stable enough for a read-only metadata audit. The previous complete index is retained.")
    }

    private func closedAuditFile(_ name: String, in parent: Int32, maximum: Int64,
                                 prefixBytes: Int) throws -> ClosedAuditFile {
        try Task.checkCancellation()
        try SourceFileAccess.validate(components: [name])
        let before = try SourceFileAccess.entryInformation(in: parent, name: name)
        guard SourceFileAccess.isRegular(before), before.st_uid == getuid(),
              before.st_mode & 0o022 == 0, !SourceFileAccess.isExcludedByFlags(before),
              before.st_size >= 0, before.st_size <= maximum else { throw closedAuditFailure() }
        let descriptor = name.withCString {
            Darwin.openat(parent, $0, O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC)
        }
        guard descriptor >= 0 else { throw closedAuditFailure() }
        defer { Darwin.close(descriptor) }
        let opened = try SourceFileAccess.information(descriptor)
        guard SourceFileAccess.unchanged(before, opened) else { throw closedAuditFailure() }
        var hasher = SHA256()
        var prefix = Data()
        var observed: Int64 = 0
        var buffer = [UInt8](repeating: 0, count: 65_536)
        while true {
            try Task.checkCancellation()
            let count = buffer.withUnsafeMutableBytes { Darwin.read(descriptor, $0.baseAddress, $0.count) }
            if count < 0 && errno == EINTR { continue }
            guard count >= 0 else { throw closedAuditFailure() }
            if count == 0 { break }
            guard observed <= before.st_size - Int64(count) else { throw closedAuditFailure() }
            observed += Int64(count)
            let chunk = Data(buffer.prefix(count))
            hasher.update(data: chunk)
            if prefix.count < prefixBytes { prefix.append(chunk.prefix(prefixBytes - prefix.count)) }
        }
        let after = try SourceFileAccess.information(descriptor)
        let current = try SourceFileAccess.entryInformation(in: parent, name: name)
        guard observed == before.st_size, SourceFileAccess.unchanged(before, after),
              SourceFileAccess.unchanged(before, current) else { throw closedAuditFailure() }
        let sha256 = hasher.finalize().map { String(format: "%02x", $0) }.joined()
        return ClosedAuditFile(info: before, sha256: sha256, prefix: prefix)
    }

    private func closedAuditSnapshot(_ directory: URL) throws -> ClosedAuditSnapshot {
        try Task.checkCancellation()
        guard lockDescriptor >= 0, let generation = UUID(uuidString: directory.lastPathComponent),
              directory.standardizedFileURL.path == generationURL(generation).path else { throw closedAuditFailure() }
        let rootFD = try SourceFileAccess.openAbsoluteDirectory(root)
        defer { Darwin.close(rootFD) }
        let rootInfo = try SourceFileAccess.information(rootFD)
        let generationsInfo = try SourceFileAccess.entryInformation(in: rootFD, name: "generations")
        let generationsFD = try SourceFileAccess.openDirectory(in: rootFD, name: "generations", expected: generationsInfo)
        defer { Darwin.close(generationsFD) }
        let name = generation.uuidString.lowercased()
        let generationInfo = try SourceFileAccess.entryInformation(in: generationsFD, name: name)
        let generationFD = try SourceFileAccess.openDirectory(in: generationsFD, name: name, expected: generationInfo)
        defer { Darwin.close(generationFD) }
        let directories: [stat] = [rootInfo, generationsInfo, generationInfo]
        for info in directories {
            guard SourceFileAccess.isDirectory(info), info.st_uid == getuid(),
                  info.st_mode & 0o7777 == 0o700, !SourceFileAccess.isExcludedByFlags(info) else { throw closedAuditFailure() }
        }
        let lock = try closedAuditFile("engine.lock", in: rootFD, maximum: 0, prefixBytes: 0)
        let heldLock = try SourceFileAccess.information(lockDescriptor)
        guard lock.info.st_mode & 0o7777 == 0o600,
              SourceFileAccess.unchanged(lock.info, heldLock) else { throw closedAuditFailure() }
        let owner = try closedAuditFile("owner.json", in: generationFD, maximum: 1_024, prefixBytes: 1_024)
        guard owner.info.st_mode & 0o7777 == 0o600 else { throw closedAuditFailure() }
        let marker = try JSONDecoder().decode(GenerationOwner.self, from: owner.prefix)
        guard marker.version == 1, marker.app == "com.alvarovillalbaa.Findlet",
              marker.generation == generation else { throw closedAuditFailure() }
        let database = try closedAuditFile("index.sqlite", in: generationFD, maximum: Int64.max, prefixBytes: 100)
        guard database.prefix.count == 100,
              database.prefix.prefix(16) == Data("SQLite format 3\0".utf8) else { throw closedAuditFailure() }
        var sidecars: [ClosedAuditSidecar] = []
        for suffix in ["-wal", "-shm", "-journal"] {
            let sidecarName = "index.sqlite" + suffix
            var info = stat()
            let status = sidecarName.withCString { Darwin.fstatat(generationFD, $0, &info, AT_SYMLINK_NOFOLLOW) }
            if status == 0 {
                let file = try closedAuditFile(sidecarName, in: generationFD, maximum: 0, prefixBytes: 0)
                sidecars.append(ClosedAuditSidecar(name: sidecarName, file: file))
            } else {
                guard errno == ENOENT else { throw closedAuditFailure() }
                sidecars.append(ClosedAuditSidecar(name: sidecarName, file: nil))
            }
        }
        let currentRootFD = try SourceFileAccess.openAbsoluteDirectory(root)
        defer { Darwin.close(currentRootFD) }
        let currentRoot = try SourceFileAccess.information(currentRootFD)
        let currentGenerations = try SourceFileAccess.entryInformation(in: rootFD, name: "generations")
        let currentGeneration = try SourceFileAccess.entryInformation(in: generationsFD, name: name)
        let currentOwner = try SourceFileAccess.entryInformation(in: generationFD, name: "owner.json")
        let currentDatabase = try SourceFileAccess.entryInformation(in: generationFD, name: "index.sqlite")
        guard sameClosedAuditDirectory(rootInfo, currentRoot),
              sameClosedAuditDirectory(generationsInfo, currentGenerations),
              sameClosedAuditDirectory(generationInfo, currentGeneration),
              SourceFileAccess.unchanged(owner.info, currentOwner),
              SourceFileAccess.unchanged(database.info, currentDatabase) else { throw closedAuditFailure() }
        return ClosedAuditSnapshot(rootInfo: rootInfo, generationsInfo: generationsInfo, generationInfo: generationInfo,
                                   lock: lock, owner: owner, database: database, sidecars: sidecars)
    }

    private func sameClosedAuditDirectory(_ left: stat, _ right: stat) -> Bool {
        // Existing summary reads can reapply private directory permissions.
        // Bind the private inode rather than unrelated directory timestamps.
        SourceFileAccess.sameObject(left, right) && left.st_uid == right.st_uid &&
        left.st_mode == right.st_mode && left.st_flags == right.st_flags
    }

    private func sameClosedAuditFile(_ left: ClosedAuditFile, _ right: ClosedAuditFile) -> Bool {
        SourceFileAccess.unchanged(left.info, right.info) && left.sha256 == right.sha256 && left.prefix == right.prefix
    }

    private func sameClosedAudit(_ left: ClosedAuditSnapshot, _ right: ClosedAuditSnapshot) -> Bool {
        guard sameClosedAuditDirectory(left.rootInfo, right.rootInfo),
              sameClosedAuditDirectory(left.generationsInfo, right.generationsInfo),
              sameClosedAuditDirectory(left.generationInfo, right.generationInfo),
              sameClosedAuditFile(left.lock, right.lock), sameClosedAuditFile(left.owner, right.owner),
              sameClosedAuditFile(left.database, right.database), left.sidecars.count == right.sidecars.count else { return false }
        for index in left.sidecars.indices {
            let before = left.sidecars[index], after = right.sidecars[index]
            guard before.name == after.name else { return false }
            switch (before.file, after.file) {
            case (nil, nil): continue
            case (.some(let a), .some(let b)):
                guard sameClosedAuditFile(a, b) else { return false }
            default: return false
            }
        }
        return true
    }

    private func environment(_ runtime: Runtime, directory: URL) throws -> [String: String] {
        let temporary = directory.appendingPathComponent("tmp", isDirectory: true)
        try createPrivateDirectory(temporary)
        var environment = [
            "PATH": runtime.node.deletingLastPathComponent().path + ":/usr/bin:/bin:/usr/sbin:/sbin",
            "TMPDIR": temporary.path, "QMD_CONFIG_DIR": directory.appendingPathComponent("config").path,
            "INDEX_PATH": directory.appendingPathComponent("index.sqlite").path,
            "XDG_CACHE_HOME": root.appendingPathComponent("cache").path,
            "QMD_FORCE_CPU": "1", "GGML_METAL_NO_RESIDENCY": "1", "NO_COLOR": "1", "LANG": "en_US.UTF-8",
        ]
        if let inheritedHome = ProcessInfo.processInfo.environment["HOME"] { environment["HOME"] = inheritedHome }
        return environment
    }

    private func validateRuntime(_ configuration: RuntimeConfiguration) throws -> Runtime {
        let node = try localURL(configuration.nodePath)
        guard manager.isExecutableFile(atPath: node.path) else { throw FindletError.message("Choose an executable Node 22 or newer runtime.") }
        let package = try localURL(configuration.qmdPackagePath)
        guard !node.path.hasPrefix(root.path + "/"), !package.path.hasPrefix(root.path + "/") else {
            throw FindletError.message("Keep Node and QMD installations outside Findlet's generated-data directory.")
        }
        try requireDirectory(package)
        let metadata = try read(package.appendingPathComponent("package.json"), limit: 1_024 * 1_024)
        guard let info = try JSONSerialization.jsonObject(with: metadata) as? [String: Any],
              info["name"] as? String == "@tobilu/qmd", info["version"] as? String == QMDContract.supportedVersion else {
            throw FindletError.message("Choose the installed @tobilu/qmd 2.8.3 package directory.")
        }
        let entry = package.appendingPathComponent("dist/cli/qmd.js").resolvingSymlinksInPath()
        guard entry.path.hasPrefix(package.path + "/") else { throw FindletError.message("The QMD entry must remain inside its package.") }
        let entryData = try read(entry, limit: 8 * 1_024 * 1_024)
        let sdk = package.appendingPathComponent("dist/index.js").resolvingSymlinksInPath()
        guard sdk.path.hasPrefix(package.path + "/") else { throw FindletError.message("The QMD SDK must remain inside its package.") }
        let sdkData = try read(sdk, limit: 8 * 1_024 * 1_024)
        let stamp = hash([node.path, try fileStamp(node), entry.path, hashData(metadata), hashData(entryData), hashData(sdkData)])
        return Runtime(node: node, entry: entry, sdk: sdk, stamp: stamp)
    }

    private func validateModels(_ configuration: RuntimeConfiguration) throws -> Models {
        guard configuration.modelPreparationAccepted else { throw FindletError.message("Confirm local model preparation in Settings first.") }
        let paths = ["embed": configuration.embeddingModelPath, "generate": configuration.expansionModelPath, "rerank": configuration.rerankerModelPath]
        var values: [String: String] = [:], stamps: [String] = []
        for key in paths.keys.sorted() {
            let file = try localURL(paths[key]!)
            guard !file.path.hasPrefix(root.path + "/") else { throw FindletError.message("Keep model files outside Findlet's generated-data directory.") }
            try requireRegular(file)
            let handle = try FileHandle(forReadingFrom: file)
            let magic: Data
            do { magic = try handle.read(upToCount: 4) ?? Data(); try handle.close() }
            catch { try? handle.close(); throw error }
            guard magic == Data("GGUF".utf8) else { throw FindletError.message("Each model must be an existing local GGUF file.") }
            values[key] = file.path; stamps.append(key + ":" + file.path + ":" + (try fileStamp(file)))
        }
        return Models(values: values, stamp: hash(stamps))
    }

    private func localURL(_ path: String) throws -> URL {
        guard path.hasPrefix("/"), !path.contains("\0"), path.utf8.count < 16_384 else {
            throw FindletError.message("Choose an existing absolute local path in Settings.")
        }
        return URL(fileURLWithPath: path).standardizedFileURL.resolvingSymlinksInPath()
    }
    private func fileStamp(_ file: URL) throws -> String {
        try requireRegular(file)
        let attributes = try manager.attributesOfItem(atPath: file.path)
        return "\(attributes[.size] ?? 0):\(attributes[.modificationDate] ?? Date.distantPast)"
    }
    private func hash(_ strings: [String]) -> String { hashData(Data(strings.joined(separator: "\0").utf8)) }
    private func hashData(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
    private func check(_ operationEpoch: Int) throws {
        try Task.checkCancellation()
        guard operationEpoch == epoch else { throw CancellationError() }
    }
    private func describe(_ state: State) -> IndexSummary {
        IndexSummary(documentCount: state.manifest.documents.count, updatedAt: state.manifest.createdAt, embeddingReady: state.manifest.embeddingReady)
    }
}
