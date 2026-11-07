import CryptoKit
import Darwin
import Foundation
import FindletCore

// Tier 3 integration: production services, actual QMD, authored disposable files.
// This executable has no AppKit entry point or user settings/bookmark access.

private struct HarnessFailure: Error { let code: String }

private func require(_ value: Bool, _ code: String) throws {
    if !value { throw HarnessFailure(code: code) }
}

private func digest(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

private func isHex(_ value: String, count: Int) -> Bool {
    value.utf8.count == count && value.allSatisfy { "0123456789abcdef".contains($0) }
}

private struct FileIdentity: Codable, Equatable {
    let device: String
    let inode: String
    let uid: UInt32
    let mode: String
    let bytes: Int64
    let mtimeSeconds: String
    let mtimeNanoseconds: String
    let ctimeSeconds: String
    let ctimeNanoseconds: String

    init(_ value: stat) {
        device = String(value.st_dev); inode = String(value.st_ino)
        uid = value.st_uid; mode = String(format: "%04o", UInt32(value.st_mode & 0o7777))
        bytes = Int64(value.st_size)
        mtimeSeconds = String(value.st_mtimespec.tv_sec)
        mtimeNanoseconds = String(value.st_mtimespec.tv_nsec)
        ctimeSeconds = String(value.st_ctimespec.tv_sec)
        ctimeNanoseconds = String(value.st_ctimespec.tv_nsec)
    }

    func sameExceptCTime(_ other: Self) -> Bool {
        device == other.device && inode == other.inode && uid == other.uid &&
        mode == other.mode && bytes == other.bytes &&
        mtimeSeconds == other.mtimeSeconds && mtimeNanoseconds == other.mtimeNanoseconds
    }
}

private struct DirectoryIdentity: Codable, Equatable {
    let device: String
    let inode: String
    let uid: UInt32
    let mode: String

    init(_ value: stat) {
        device = String(value.st_dev); inode = String(value.st_ino)
        uid = value.st_uid; mode = String(format: "%04o", UInt32(value.st_mode & 0o7777))
    }
}

private struct FileProof: Codable, Equatable {
    let relativePath: String
    let kind: String
    let identity: FileIdentity
    let sha256: String
    var linkTargetRelative: String? = nil
}

private struct ReadFile {
    let data: Data
    let proof: FileProof
}

private func entry(_ parent: Int32, _ name: String) throws -> stat {
    var value = stat()
    let status = name.withCString { fstatat(parent, $0, &value, AT_SYMLINK_NOFOLLOW) }
    try require(status == 0, "file_entry_unavailable")
    return value
}

private func readRegular(parent: Int32, name: String, label: String, maximum: Int,
                         privateFile: Bool, retain: Bool = true) throws -> ReadFile {
    let before = try entry(parent, name)
    try require(before.st_mode & mode_t(S_IFMT) == mode_t(S_IFREG) &&
                before.st_size >= 0 && before.st_size <= Int64(maximum), "regular_file_bound")
    if privateFile {
        try require(before.st_uid == getuid() && before.st_mode & 0o7777 == 0o600, "private_file_owner_mode")
    }
    let fd = name.withCString { openat(parent, $0, O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC) }
    try require(fd >= 0, "regular_file_open_failed")
    defer { Darwin.close(fd) }
    var opened = stat()
    try require(fstat(fd, &opened) == 0 && FileIdentity(opened) == FileIdentity(before), "file_changed_at_open")
    var bytes = Data()
    var hasher = SHA256()
    var count = 0
    var buffer = [UInt8](repeating: 0, count: 65_536)
    while true {
        let got = buffer.withUnsafeMutableBytes { Darwin.read(fd, $0.baseAddress, $0.count) }
        if got < 0 && errno == EINTR { continue }
        try require(got >= 0, "file_read_failed")
        if got == 0 { break }
        try require(count <= maximum - got, "file_read_limit")
        let chunk = Data(buffer.prefix(got))
        hasher.update(data: chunk)
        if retain { bytes.append(chunk) }
        count += got
    }
    var after = stat()
    let current = try entry(parent, name)
    try require(fstat(fd, &after) == 0 && FileIdentity(before) == FileIdentity(after) &&
                FileIdentity(current) == FileIdentity(before) && Int64(count) == Int64(before.st_size),
                "file_changed_during_read")
    let hash = hasher.finalize().map { String(format: "%02x", $0) }.joined()
    return ReadFile(data: bytes, proof: FileProof(relativePath: label, kind: "regular",
                                                identity: FileIdentity(before), sha256: hash))
}

private final class OwnedRoot {
    let url: URL
    let fd: Int32
    let identity: DirectoryIdentity
    private let nonce: Data
    private let marker: FileProof
    var directories: [String: DirectoryIdentity] = [:]

    init(path: String, nonce: String) throws {
        let value = URL(fileURLWithPath: path, isDirectory: true)
        try require(path.hasPrefix("/") && !path.utf8.contains(0) &&
                    value.standardizedFileURL.path == path && value.resolvingSymlinksInPath().path == path,
                    "root_not_physical")
        let descriptor = try SourceFileAccess.openAbsoluteDirectory(value)
        do {
            let info = try SourceFileAccess.information(descriptor)
            try require(info.st_uid == getuid() && info.st_mode & 0o7777 == 0o700, "root_owner_mode")
            let read = try readRegular(parent: descriptor, name: ".owner", label: ".owner",
                                       maximum: 32, privateFile: true)
            try require(read.data == Data(nonce.utf8) && read.data.count == 32, "root_nonce_mismatch")
            self.url = value; self.fd = descriptor; self.identity = DirectoryIdentity(info)
            self.nonce = Data(nonce.utf8); self.marker = read.proof
        } catch {
            Darwin.close(descriptor)
            throw error
        }
    }

    deinit { Darwin.close(fd) }

    func check() throws {
        let current = try SourceFileAccess.openAbsoluteDirectory(url)
        defer { Darwin.close(current) }
        let info = try SourceFileAccess.information(current)
        let held = try SourceFileAccess.information(fd)
        try require(DirectoryIdentity(info) == identity && DirectoryIdentity(held) == identity,
                    "root_identity_changed")
        let read = try readRegular(parent: fd, name: ".owner", label: ".owner", maximum: 32, privateFile: true)
        try require(read.proof == marker && read.data == nonce, "root_marker_changed")
    }

    func createDirectory(_ name: String) throws {
        try check()
        try SourceFileAccess.validate(components: [name])
        try require(mkdirat(fd, name, 0o700) == 0, "owned_directory_not_new")
        let info = try entry(fd, name)
        try require(info.st_mode & mode_t(S_IFMT) == mode_t(S_IFDIR) &&
                    info.st_uid == getuid() && info.st_mode & 0o7777 == 0o700, "owned_directory_invalid")
        directories[name] = DirectoryIdentity(info)
    }

    func verifyDirectories() throws {
        try check()
        for (name, expected) in directories {
            let info = try entry(fd, name)
            try require(info.st_mode & mode_t(S_IFMT) == mode_t(S_IFDIR) &&
                        DirectoryIdentity(info) == expected, "owned_directory_changed")
        }
    }

    private func parent(_ relative: String) throws -> (Int32, String) {
        try check()
        let components = relative.split(separator: "/", omittingEmptySubsequences: false).map(String.init)
        try SourceFileAccess.validate(components: components)
        var descriptor = fcntl(fd, F_DUPFD_CLOEXEC, 0)
        try require(descriptor >= 0, "root_descriptor_duplicate_failed")
        do {
            var traversed: [String] = []
            for component in components.dropLast() {
                let child = component.withCString { openat(descriptor, $0, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC) }
                try require(child >= 0, "owned_parent_unavailable")
                Darwin.close(descriptor); descriptor = child
                traversed.append(component)
                let info = try SourceFileAccess.information(descriptor)
                try require(info.st_uid == getuid() && info.st_mode & 0o7777 == 0o700, "owned_parent_mode")
                if traversed.count == 1, let expected = directories[component] {
                    try require(DirectoryIdentity(info) == expected, "owned_parent_identity_changed")
                }
            }
            return (descriptor, components.last!)
        } catch {
            Darwin.close(descriptor)
            throw error
        }
    }

    func exists(_ relative: String) throws -> Bool {
        let (parentFD, name) = try parent(relative)
        defer { Darwin.close(parentFD) }
        var info = stat()
        if fstatat(parentFD, name, &info, AT_SYMLINK_NOFOLLOW) == 0 { return true }
        try require(errno == ENOENT, "owned_absence_unconfirmed")
        return false
    }

    func read(_ relative: String, maximum: Int = 131_072) throws -> ReadFile {
        let (parentFD, name) = try parent(relative)
        defer { Darwin.close(parentFD) }
        return try readRegular(parent: parentFD, name: name, label: relative,
                               maximum: maximum, privateFile: true)
    }

    func snapshot(_ relative: String) throws -> FileProof {
        let (parentFD, name) = try parent(relative)
        defer { Darwin.close(parentFD) }
        let info = try entry(parentFD, name)
        if info.st_mode & mode_t(S_IFMT) == mode_t(S_IFLNK) {
            try require(info.st_uid == getuid(), "owned_symlink_owner")
            var buffer = [UInt8](repeating: 0, count: 512)
            let count = name.withCString { namePointer in
                buffer.withUnsafeMutableBytes { bytes in
                    readlinkat(parentFD, namePointer,
                               bytes.baseAddress!.assumingMemoryBound(to: CChar.self), bytes.count)
                }
            }
            try require(count > 0 && count < buffer.count, "owned_symlink_bound")
            let bytes = Data(buffer.prefix(count))
            try require(FileIdentity(try entry(parentFD, name)) == FileIdentity(info), "owned_symlink_changed")
            guard let target = String(data: bytes, encoding: .utf8) else { throw HarnessFailure(code: "owned_symlink_utf8") }
            return FileProof(relativePath: relative, kind: "symlink", identity: FileIdentity(info),
                             sha256: digest(bytes), linkTargetRelative: target)
        }
        return try readRegular(parent: parentFD, name: name, label: relative,
                               maximum: 65_536, privateFile: true).proof
    }

    func createFile(_ relative: String, data: Data) throws -> FileProof {
        try require(data.count <= 65_536, "authored_file_bound")
        let (parentFD, name) = try parent(relative)
        defer { Darwin.close(parentFD) }
        let descriptor = name.withCString {
            openat(parentFD, $0, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0o600)
        }
        try require(descriptor >= 0, "authored_file_not_new")
        defer { Darwin.close(descriptor) }
        let initial = try SourceFileAccess.information(descriptor)
        try data.withUnsafeBytes { raw in
            var position = 0
            while position < raw.count {
                let count = Darwin.write(descriptor, raw.baseAddress!.advanced(by: position), raw.count - position)
                if count < 0 && errno == EINTR { continue }
                try require(count > 0, "authored_file_write_failed")
                position += count
            }
        }
        try require(fsync(descriptor) == 0, "authored_file_flush_failed")
        let current = try readRegular(parent: parentFD, name: name, label: relative,
                                      maximum: 65_536, privateFile: true).proof
        try require(current.identity.device == String(initial.st_dev) &&
                    current.identity.inode == String(initial.st_ino) && current.sha256 == digest(data),
                    "authored_file_replaced")
        return current
    }

    func createSymlink(_ relative: String, target: String) throws -> FileProof {
        let (parentFD, name) = try parent(relative)
        defer { Darwin.close(parentFD) }
        try require(target == "../decoy/outside.md" && symlinkat(target, parentFD, name) == 0,
                    "authored_symlink_not_new")
        return try snapshot(relative)
    }

    func removeOwned(_ expected: FileProof) throws {
        try require(try snapshot(expected.relativePath) == expected, "owned_removal_identity_changed")
        let (parentFD, name) = try parent(expected.relativePath)
        defer { Darwin.close(parentFD) }
        try require(unlinkat(parentFD, name, 0) == 0, "owned_file_remove_failed")
    }

    func moveOwned(_ expected: FileProof, to destination: String) throws -> FileProof {
        try require(try snapshot(expected.relativePath) == expected, "owned_move_identity_changed")
        let (sourceFD, sourceName) = try parent(expected.relativePath)
        defer { Darwin.close(sourceFD) }
        let (targetFD, targetName) = try parent(destination)
        defer { Darwin.close(targetFD) }
        try require(renameatx_np(sourceFD, sourceName, targetFD, targetName, UInt32(RENAME_EXCL)) == 0,
                    "owned_exclusive_move_failed")
        let current = try snapshot(destination)
        try require(current.sha256 == expected.sha256 &&
                    current.identity.sameExceptCTime(expected.identity), "owned_move_payload_changed")
        return current
    }

    func names(in relative: String) throws -> [String] {
        let (parentFD, name) = try parent(relative)
        defer { Darwin.close(parentFD) }
        let descriptor = name.withCString { openat(parentFD, $0, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC) }
        try require(descriptor >= 0, "owned_directory_list_failed")
        defer { Darwin.close(descriptor) }
        var names: [String] = []
        try SourceFileAccess.forEachEntry(in: descriptor) { names.append($0) }
        return names.sorted()
    }
}

private func absoluteFile(_ url: URL, label: String, maximum: Int, executable: Bool = false,
                          retain: Bool = false) throws -> ReadFile {
    let descriptor = try SourceFileAccess.openAbsoluteDirectory(url.deletingLastPathComponent())
    defer { Darwin.close(descriptor) }
    let value = try readRegular(parent: descriptor, name: url.lastPathComponent, label: label,
                                maximum: maximum, privateFile: false, retain: retain)
    if executable {
        let info = try entry(descriptor, url.lastPathComponent)
        try require(info.st_mode & 0o111 != 0, "selected_node_not_executable")
    }
    return value
}

private struct RuntimeProof: Codable, Equatable {
    let node: FileProof
    let packageJSON: FileProof
    let cliEntry: FileProof
    let sdk: FileProof
}

private struct DocumentProof: Codable, Equatable {
    let id: String
    let folderID: String
    let relativePath: String
    let snapshotName: String
    let title: String
}

private struct PointerValue: Decodable { let version: Int; let generation: UUID }
private struct StateValue: Decodable {
    let manifest: IndexManifest
    let runtimeStamp: String
    let modelStamp: String?
}
private struct PointerProof: Codable {
    let file: FileProof
    let version: Int
    let generation: String
}
private struct StateProof: Codable {
    let file: FileProof
    let version: Int
    let generation: String
    let documentCount: Int
    let embeddingReady: Bool
    let documents: [DocumentProof]
    let corpusRelative: String
    let databaseRelative: String
    let configRelative: String
}
private struct IndexProof: Codable {
    let schemaVersion: Int
    let sourceCommit: String
    let ownerNonceSHA256: String
    let rootIdentity: DirectoryIdentity
    let producerPID: Int32
    let folderID: String
    let directories: [String: DirectoryIdentity]
    let expectedFiles: [FileProof]
    let runtime: RuntimeProof
    let pointer: PointerProof
    let state: StateProof
}
private struct StageEvent: Codable { let stage: String; let elapsedMs: UInt64 }
private struct QueryProof: Codable {
    let ordinal: Int
    let documentID: String
    let relativePath: String
    let sourceBytes: Int64
    let sourceSHA256: String
    let snippetBytes: Int
    let snippetSHA256: String
    let line: Int
    let scoreFinite: Bool
    let resolvedExactOwnedOriginal: Bool
}
private enum FailureKind: String, Encodable {
    case findletMessage = "findlet_message"
    case cancellation, decoding, other
}
private struct FailureDiagnostic: Encodable {
    let stage: String
    let kind: FailureKind
    let messageSHA256: String?
}
private struct Report: Encodable {
    let schemaVersion = 1
    var sourceCommit: String?
    var phase = "unknown"
    var caseID = "unknown"
    var accepted = false
    var checks: [String: Bool] = [:]
    var stageEvents: [StageEvent] = []
    let engineRootRelative = "engine"
    let fixtureRootRelative = "authored"
    var expectedFiles: [FileProof] = []
    var runtime: RuntimeProof?
    var pointer: PointerProof?
    var state: StateProof?
    var queryProofs: [QueryProof] = []
    var proofFile: FileProof?
    var errors: [String] = []
    var failureDiagnostic: FailureDiagnostic?
    let proofLimits = [
        "Tier 3 app-less production-service integration on authored disposable documents; no AppKit app, user selection, existing bookmarks/settings, private folder, model or semantic acceptance.",
        "Only an ordinary Foundation bookmark of the owned authored folder is created. Bookmark bytes remain in memory and private production state, never this report or the harness proof.",
        "Queries, document bodies and snippets are not retained; only authored relative paths, IDs, bounded metadata and hashes are reported.",
        "The lifecycle probe moves one authored original to owned quarantine and restores the same inode. Its ctime and authored-directory timestamps may change; bytes, inode, mode and mtime are checked.",
        "Runtime fingerprints cover the selected Node, package.json, CLI and SDK files. Package-tree/native-binding proof is owned by the outer controller.",
        "Production QMD stderr is consumed internally and is not exposed as a retained raw stream here. Engine locks close at process exit; the controller must reap each session before the next.",
        "Filesystem checks are boundary observations, not continuous snapshots, sandbox enforcement, host-wide process or network-offline attestations."
    ]

    enum CodingKeys: String, CodingKey {
        case schemaVersion, sourceCommit, phase, accepted, checks, stageEvents
        case engineRootRelative, fixtureRootRelative, expectedFiles, runtime, pointer, state
        case queryProofs, proofFile, errors, failureDiagnostic, proofLimits
        case caseID = "case"
    }
}

private struct Arguments {
    let phase: String
    let root: URL
    let node: URL
    let qmd: URL

    init() throws {
        let raw = Array(CommandLine.arguments.dropFirst())
        try require(raw.count == 8, "invalid_arguments")
        var values: [String: String] = [:]
        for index in stride(from: 0, to: raw.count, by: 2) {
            let key = raw[index], value = raw[index + 1]
            try require(["--phase", "--root", "--node", "--qmd"].contains(key) &&
                        values[key] == nil && !value.isEmpty && value.utf8.count < 16_384 &&
                        !value.utf8.contains(0), "invalid_arguments")
            values[key] = value
        }
        guard let phase = values["--phase"], let root = values["--root"],
              let node = values["--node"], let qmd = values["--qmd"] else {
            throw HarnessFailure(code: "invalid_arguments")
        }
        try require(phase == "index" || phase == "lifecycle", "invalid_phase")
        func physical(_ path: String, directory: Bool) throws -> URL {
            let url = URL(fileURLWithPath: path, isDirectory: directory)
            try require(path.hasPrefix("/") && url.standardizedFileURL.path == path &&
                        url.resolvingSymlinksInPath().path == path, "argument_not_physical")
            return url
        }
        self.phase = phase
        self.root = try physical(root, directory: true)
        self.node = try physical(node, directory: false)
        self.qmd = try physical(qmd, directory: true)
    }
}

@MainActor
private final class Harness {
    private static let folderString = "D47AF59C-6411-4BAA-9824-C6A2B1D8E27B"
    private static let paths = ["alpha.md", "notes-東京.markdown", "plain.txt"]
    private static let ids = [
        "0556f1ae-5314-898a-bf90-51767e53472d",
        "7dea72c0-3913-89fa-827e-4f110b7595f7",
        "65cf6866-2808-8628-9bde-5609beb4a53d"
    ]
    private static let queries = ["quartzvelvetalpha", "cobaltlilacbeta"]
    private static let authored: [(String, String)] = [
        ("authored/alpha.md", "# Authored Alpha\n\nquartzvelvetalpha is the first authored keyword.\n"),
        ("authored/notes-東京.markdown", "# Café Notes\n\ncobaltlilacbeta — café naïve; authored Unicode only.\n"),
        ("authored/plain.txt", "Plain authored UTF-8 document without either rare marker.\n"),
        ("authored/.hidden.md", "Hidden authored negative: quartzvelvetalpha cobaltlilacbeta.\n"),
        ("decoy/outside.md", "Outside owned decoy: quartzvelvetalpha cobaltlilacbeta.\n")
    ]
    private let args: Arguments
    private let owner: OwnedRoot
    private let sourceCommit: String
    private let nonce: String
    private let start = DispatchTime.now().uptimeNanoseconds
    private var stage = "initialization"
    private var report: Report

    init(args: Arguments, sourceCommit: String, nonce: String) throws {
        self.args = args; self.sourceCommit = sourceCommit; self.nonce = nonce
        owner = try OwnedRoot(path: args.root.path, nonce: nonce)
        var initial = Report()
        initial.phase = args.phase
        initial.caseID = args.phase == "index" ? "K01" : "K02"
        initial.sourceCommit = sourceCommit
        report = initial
    }

    private func event(_ name: String) {
        stage = name
        report.stageEvents.append(StageEvent(stage: name, elapsedMs: (DispatchTime.now().uptimeNanoseconds - start) / 1_000_000))
    }

    private func checked(_ name: String, _ condition: Bool) throws {
        report.checks[name] = condition
        try require(condition, "check_" + name + "_failed")
    }

    private func documents() -> [DocumentProof] {
        zip(Self.paths, Self.ids).map { pair in
            let (path, id) = pair
            return DocumentProof(id: id, folderID: Self.folderString.lowercased(), relativePath: path,
                                 snapshotName: id + ".md", title: path)
        }
    }

    private func runtimeProof() throws -> RuntimeProof {
        try owner.check()
        let engine = args.root.appendingPathComponent("engine").path
        try require(args.node.path != engine && !args.node.path.hasPrefix(engine + "/") &&
                    args.qmd.path != engine && !args.qmd.path.hasPrefix(engine + "/"),
                    "runtime_inside_engine")
        let node = try absoluteFile(args.node, label: "selected-node", maximum: 256 * 1024 * 1024,
                                    executable: true)
        let metadata = try absoluteFile(args.qmd.appendingPathComponent("package.json"),
                                        label: "selected-qmd-package-json", maximum: 1024 * 1024, retain: true)
        let json = try JSONSerialization.jsonObject(with: metadata.data) as? [String: Any]
        try require((json?["name"] as? String) == "@tobilu/qmd" &&
                    (json?["version"] as? String) == "2.8.3", "selected_qmd_version")
        let cli = try absoluteFile(args.qmd.appendingPathComponent("dist/cli/qmd.js"),
                                   label: "selected-qmd-cli", maximum: 8 * 1024 * 1024)
        let sdk = try absoluteFile(args.qmd.appendingPathComponent("dist/index.js"),
                                   label: "selected-qmd-sdk", maximum: 8 * 1024 * 1024)
        return RuntimeProof(node: node.proof, packageJSON: metadata.proof, cliEntry: cli.proof, sdk: sdk.proof)
    }

    private func runtimeConfiguration() -> RuntimeConfiguration {
        var value = RuntimeConfiguration()
        value.nodePath = args.node.path; value.qmdPackagePath = args.qmd.path
        return value
    }

    private func captureState() throws -> (PointerProof, StateProof) {
        let pointerFile = try owner.read("engine/current.json", maximum: 1024)
        let pointer = try JSONDecoder().decode(PointerValue.self, from: pointerFile.data)
        let generation = pointer.generation.uuidString.lowercased()
        let prefix = "engine/generations/" + generation
        let stateFile = try owner.read(prefix + "/state.json")
        let state = try JSONDecoder().decode(StateValue.self, from: stateFile.data)
        let actualDocuments = state.manifest.documents.map {
            DocumentProof(id: $0.id.uuidString.lowercased(), folderID: $0.folderID.uuidString.lowercased(),
                          relativePath: $0.relativePath, snapshotName: $0.snapshotName, title: $0.title)
        }
        try require(pointer.version == 1 && state.manifest.version == 1 &&
                    state.manifest.generation == pointer.generation &&
                    state.manifest.folders.count == 1 &&
                    state.manifest.folders.first?.id.uuidString.lowercased() == Self.folderString.lowercased() &&
                    actualDocuments == documents() && !state.manifest.embeddingReady &&
                    state.modelStamp == nil && isHex(state.runtimeStamp, count: 64),
                    "state_manifest_contract")
        return (PointerProof(file: pointerFile.proof, version: 1, generation: generation),
                StateProof(file: stateFile.proof, version: 1, generation: generation,
                           documentCount: actualDocuments.count, embeddingReady: false,
                           documents: actualDocuments, corpusRelative: prefix + "/corpus",
                           databaseRelative: prefix + "/index.sqlite", configRelative: prefix + "/config/findlet.yml"))
    }

    private func sourceProofs() throws -> [FileProof] {
        try (Self.authored.map(\.0) + ["authored/outside-link.md"]).sorted().map { try owner.snapshot($0) }
    }

    private func queries(_ engine: FindletEngine, expected: [FileProof]) async throws -> [SearchHit] {
        var actual: [SearchHit] = []
        for ordinal in 0..<Self.queries.count {
            let hits = try await engine.search(Self.queries[ordinal], mode: .keyword, runtime: runtimeConfiguration())
            let path = Self.paths[ordinal], id = Self.ids[ordinal]
            try require(hits.count == 1 && hits[0].documentID.uuidString.lowercased() == id &&
                        hits[0].path == path && hits[0].title == path && hits[0].score.isFinite &&
                        hits[0].line >= 1, "keyword_result_contract")
            let url = try await engine.sourceURL(for: hits[0])
            let relative = "authored/" + path
            try require(url.standardizedFileURL == args.root.appendingPathComponent(relative).standardizedFileURL,
                        "resolved_original_outside_fixture")
            let file = try owner.read(relative, maximum: 65_536)
            guard let initial = expected.first(where: { $0.relativePath == relative }) else {
                throw HarnessFailure(code: "missing_expected_source")
            }
            try require(file.proof == initial, "resolved_source_changed")
            let snippet = Data(hits[0].snippet.utf8)
            report.queryProofs.append(QueryProof(ordinal: ordinal + 1, documentID: id, relativePath: path,
                sourceBytes: file.proof.identity.bytes, sourceSHA256: file.proof.sha256,
                snippetBytes: snippet.count, snippetSHA256: digest(snippet), line: hits[0].line,
                scoreFinite: true, resolvedExactOwnedOriginal: true))
            actual.append(hits[0])
        }
        return actual
    }

    private func index() async throws {
        event("create_authored_fixture")
        for name in ["authored", "decoy", "engine", "ledger", "quarantine"] {
            try owner.createDirectory(name)
        }
        for (path, text) in Self.authored { _ = try owner.createFile(path, data: Data(text.utf8)) }
        _ = try owner.createSymlink("authored/outside-link.md", target: "../decoy/outside.md")
        let sources = try sourceProofs()
        report.expectedFiles = sources
        let runtime = try runtimeProof()
        report.runtime = runtime
        let folderURL = args.root.appendingPathComponent("authored", isDirectory: true)
        let bookmark = try folderURL.bookmarkData(options: [], includingResourceValuesForKeys: nil, relativeTo: nil)
        guard let id = UUID(uuidString: Self.folderString) else { throw HarnessFailure(code: "fixed_folder_id") }
        let folder = FolderSelection(id: id, name: "Authored CI folder", bookmark: bookmark)
        let engine = FindletEngine(applicationSupport: args.root.appendingPathComponent("engine"))
        event("production_rebuild")
        let rebuilt = try await engine.rebuild(folders: [folder], runtime: runtimeConfiguration())
        try checked("rebuildThreeDocumentsWithoutModels", rebuilt.documentCount == 3 && !rebuilt.embeddingReady)
        let summary = try await engine.summary()
        try checked("summaryMatchesRebuild", summary.documentCount == 3 && !summary.embeddingReady)
        let (pointer, state) = try captureState()
        report.pointer = pointer; report.state = state
        event("production_keyword_queries_and_resolution")
        _ = try await queries(engine, expected: sources)
        let (pointerAfter, stateAfter) = try captureState()
        try checked("pointerStateStableAcrossSearch", pointerAfter.file == pointer.file && stateAfter.file == state.file)
        try checked("hiddenAndSymlinkExcluded", state.documents.count == 3 &&
                    state.documents.allSatisfy { Self.paths.contains($0.relativePath) })
        try checked("authoredSourcesUnchanged", try sourceProofs() == sources)
        try checked("runtimeSelectedFilesUnchanged", try runtimeProof() == runtime)
        try owner.verifyDirectories()
        event("persist_private_handoff")
        let proof = IndexProof(schemaVersion: 1, sourceCommit: sourceCommit, ownerNonceSHA256: digest(Data(nonce.utf8)),
            rootIdentity: owner.identity, producerPID: getpid(), folderID: Self.folderString.lowercased(),
            directories: owner.directories, expectedFiles: sources, runtime: runtime, pointer: pointer, state: state)
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        var bytes = try encoder.encode(proof); bytes.append(0x0a)
        report.proofFile = try owner.createFile("ledger/index-proof.json", data: bytes)
        try checked("privateProofCreated", report.proofFile?.identity.mode == "0600")
        try owner.check()
        try checked("rootOwnershipFinal", true)
        event("index_complete_preserved_for_parent")
    }

    private func lifecycle() async throws {
        event("load_private_handoff")
        let expectedHash = ProcessInfo.processInfo.environment["FINDLET_QMD_KEYWORD_INDEX_PROOF_SHA256"] ?? ""
        try require(isHex(expectedHash, count: 64), "handoff_hash_required")
        let handoff = try owner.read("ledger/index-proof.json", maximum: 65_536)
        try require(handoff.proof.sha256 == expectedHash, "handoff_hash_mismatch")
        let proof = try JSONDecoder().decode(IndexProof.self, from: handoff.data)
        try require(proof.schemaVersion == 1 && proof.sourceCommit == sourceCommit &&
                    proof.ownerNonceSHA256 == digest(Data(nonce.utf8)) && proof.rootIdentity == owner.identity &&
                    proof.folderID == Self.folderString.lowercased() && proof.producerPID != getpid() &&
                    Set(proof.directories.keys) == Set(["authored", "decoy", "engine", "ledger", "quarantine"]) &&
                    proof.state.documents == documents(), "handoff_contract")
        owner.directories = proof.directories
        try owner.verifyDirectories()
        report.proofFile = handoff.proof; report.expectedFiles = proof.expectedFiles
        try checked("authoredSourcesMatchPriorSession", try sourceProofs() == proof.expectedFiles)
        let runtime = try runtimeProof()
        report.runtime = runtime
        try checked("runtimeMatchesPriorSession", runtime == proof.runtime)
        let (beforePointer, beforeState) = try captureState()
        try checked("pointerStateMatchPriorSession", beforePointer.file == proof.pointer.file &&
                    beforeState.file == proof.state.file && beforePointer.generation == proof.pointer.generation)
        report.pointer = beforePointer; report.state = beforeState
        let engine = FindletEngine(applicationSupport: args.root.appendingPathComponent("engine"))
        event("reopen_production_engine")
        let summary = try await engine.summary()
        try checked("newEngineReadsThreeDocuments", summary.documentCount == 3 && !summary.embeddingReady)
        _ = try await queries(engine, expected: proof.expectedFiles)
        event("invalid_utf8_rebuild_preserves_generation")
        let invalid = try owner.createFile("authored/invalid.md", data: Data([0xff, 0xfe]))
        let folders = try currentFolders()
        var invalidRefused = false
        do { _ = try await engine.rebuild(folders: folders, runtime: runtimeConfiguration()) }
        catch let error as FindletError {
            if case .message(let message) = error {
                invalidRefused = message == "A selected Markdown or text file is not valid UTF-8. Convert it before rebuilding; originals were not changed."
            }
        } catch { invalidRefused = false }
        try owner.removeOwned(invalid)
        try checked("invalidUTF8RefusalObserved", invalidRefused)
        let (afterPointer, afterState) = try captureState()
        try checked("failedRebuildPreservesFullPointerAndState", afterPointer.file == beforePointer.file &&
                    afterState.file == beforeState.file && afterPointer.generation == beforePointer.generation)
        try checked("failedGenerationRemoved", try owner.names(in: "engine/generations") == [beforePointer.generation])
        let hits = try await queries(engine, expected: proof.expectedFiles)
        event("missing_original_resolver_refusal")
        guard let initial = proof.expectedFiles.first(where: { $0.relativePath == "authored/alpha.md" }) else {
            throw HarnessFailure(code: "missing_source_proof")
        }
        let quarantined = try owner.moveOwned(initial, to: "quarantine/alpha.md")
        var missingRefused = false
        do { _ = try await engine.sourceURL(for: hits[0]) }
        catch is FindletError { missingRefused = true }
        catch { missingRefused = false }
        let restored = try owner.moveOwned(quarantined, to: "authored/alpha.md")
        try checked("missingOriginalRefused", missingRefused)
        try checked("sameInodeOriginalRestored", restored.sha256 == initial.sha256 &&
                    restored.identity.sameExceptCTime(initial.identity))
        let resolved = try await engine.sourceURL(for: hits[0])
        try checked("restoredOriginalResolves", resolved.standardizedFileURL ==
                    args.root.appendingPathComponent("authored/alpha.md").standardizedFileURL)
        let finalSources = try sourceProofs()
        for current in finalSources {
            guard let prior = proof.expectedFiles.first(where: { $0.relativePath == current.relativePath }) else {
                throw HarnessFailure(code: "unexpected_original")
            }
            if current.relativePath == initial.relativePath {
                try require(current.sha256 == prior.sha256 && current.identity.sameExceptCTime(prior.identity),
                            "restored_original_changed")
            } else { try require(current == prior, "other_original_changed") }
        }
        report.expectedFiles = finalSources
        try checked("originalBytesModesInodesAndMTimePreserved", true)
        event("production_forget_index")
        try await engine.forgetIndex()
        let empty = try await engine.summary()
        try checked("forgetSummaryEmpty", empty.documentCount == 0 && !empty.embeddingReady)
        try checked("currentPointerAbsent", try !owner.exists("engine/current.json"))
        let remainingGenerations = try owner.names(in: "engine/generations")
        let remainingCache = try owner.names(in: "engine/cache")
        try checked("generationAndCacheEmpty", remainingGenerations.isEmpty && remainingCache.isEmpty)
        try checked("quarantineEmpty", try owner.names(in: "quarantine").isEmpty)
        try checked("sourcesRemainAfterForget", try sourceProofs() == finalSources)
        try checked("runtimeSelectedFilesUnchanged", try runtimeProof() == proof.runtime)
        try owner.verifyDirectories()
        try owner.check()
        try checked("rootOwnershipFinal", true)
        event("lifecycle_complete")
    }

    private func currentFolders() throws -> [FolderSelection] {
        // Read only the private production state. Bookmark bytes never enter a
        // report or handoff proof; the real SourceFileAccess resolver consumes them.
        let (pointer, _) = try captureState()
        let state = try owner.read("engine/generations/" + pointer.generation + "/state.json")
        return try JSONDecoder().decode(StateValue.self, from: state.data).manifest.folders
    }

    func run() async -> Report {
        do {
            try owner.check()
            if args.phase == "index" { try await index() }
            else { try await lifecycle() }
            report.accepted = true
        } catch let error as HarnessFailure {
            report.errors.append(error.code)
        } catch {
            let kind: FailureKind
            var messageSHA256: String? = nil
            if let findletError = error as? FindletError {
                switch findletError {
                case .message(let message):
                    kind = .findletMessage
                    messageSHA256 = digest(Data(message.utf8))
                }
            } else if error is CancellationError { kind = .cancellation }
            else if error is DecodingError { kind = .decoding }
            else { kind = .other }
            report.failureDiagnostic = FailureDiagnostic(stage: stage, kind: kind, messageSHA256: messageSHA256)
            report.errors.append("production_" + stage + "_refused")
        }
        return report
    }
}

@main
private struct KeywordPipelineHarness {
    @MainActor
    static func main() async {
        var report = Report()
        do {
            let source = ProcessInfo.processInfo.environment["SOURCE_COMMIT"] ?? ""
            let nonce = ProcessInfo.processInfo.environment["FINDLET_QMD_KEYWORD_NONCE"] ?? ""
            try require(isHex(source, count: 40) && isHex(nonce, count: 32), "approved_environment_required")
            let args = try Arguments()
            let harness = try Harness(args: args, sourceCommit: source, nonce: nonce)
            report = await harness.run()
        } catch let error as HarnessFailure { report.errors.append(error.code) }
        catch { report.errors.append("harness_setup_refused") }
        do {
            let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
            let body = try encoder.encode(report)
            try require(body.count <= 131_072, "report_bound")
            var output = Data("FINDLET_QMD_KEYWORD_RESULT=".utf8)
            output.append(body); output.append(0x0a)
            try FileHandle.standardOutput.write(contentsOf: output)
            Darwin.exit(report.accepted ? 0 : 1)
        } catch { Darwin.exit(2) }
    }
}
