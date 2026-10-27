import CryptoKit
import Darwin
import Foundation
import FindletCore

enum CorpusBuilder {
    private static let maximumDocuments = 2_000
    private static let maximumDocumentBytes = 2 * 1_024 * 1_024
    private static let maximumCombinedBytes = 100 * 1_024 * 1_024
    private static let maximumEntries = 100_000
    private static let maximumDepth = 64
    private static let extensions: Set<String> = ["md", "markdown", "txt"]

    private struct Candidate {
        let components: [String]
        let info: stat
        var relativePath: String { components.joined(separator: "/") }
    }

    private final class Budget {
        var visited = 0
        var documents = 0
        var bytes = 0
    }

    static func build(folders: [FolderSelection], at generationURL: URL) throws -> IndexManifest {
        try Task.checkCancellation()
        guard !folders.isEmpty, Set(folders.map(\.id)).count == folders.count else {
            throw FindletError.message("Choose at least one folder, without duplicate folder identities.")
        }
        guard let generation = UUID(uuidString: generationURL.lastPathComponent) else {
            throw FindletError.message("The new index generation has an invalid identity.")
        }
        let generationFD = try SourceFileAccess.openAbsoluteDirectory(generationURL)
        defer { Darwin.close(generationFD) }
        let generationInfo = try SourceFileAccess.information(generationFD)
        guard Darwin.mkdirat(generationFD, "corpus", mode_t(0o700)) == 0 else {
            throw FindletError.message("A fresh index corpus could not be created. The previous index is retained.")
        }
        let corpusFD = Darwin.openat(generationFD, "corpus", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        guard corpusFD >= 0 else {
            throw FindletError.message("The new index corpus could not be opened safely.")
        }
        defer { Darwin.close(corpusFD) }
        let corpusInfo = try SourceFileAccess.information(corpusFD)
        let budget = Budget()
        var documents: [IndexedDocument] = []
        let generatedDataURL = generationURL.deletingLastPathComponent().deletingLastPathComponent()
        for folder in folders.sorted(by: { $0.id.uuidString < $1.id.uuidString }) {
            try Task.checkCancellation()
            try SourceFileAccess.withRoot(folder) { root in
                guard try !SourceFileAccess.overlaps(root, with: generatedDataURL) else {
                    throw FindletError.message("Choose document folders outside Findlet's generated-data folder. A whole home folder would also include Findlet's own index.")
                }
                var candidates: [Candidate] = []
                try walk(root: root, descriptor: root.descriptor, components: [],
                         budget: budget, candidates: &candidates)
                candidates.sort { $0.relativePath.utf8.lexicographicallyPrecedes($1.relativePath.utf8) }
                for candidate in candidates {
                    try Task.checkCancellation()
                    let bytes = try read(candidate, root: root, budget: budget)
                    guard let text = String(data: bytes, encoding: .utf8) else {
                        throw FindletError.message("A selected Markdown or text file is not valid UTF-8. Convert it before rebuilding; originals were not changed.")
                    }
                    guard text.unicodeScalars.contains(where: { !qmdWhitespace.contains($0) }) else {
                        throw FindletError.message("An eligible text file is empty or whitespace-only. Add searchable text or choose a narrower folder before rebuilding.")
                    }
                    let document = IndexedDocument(
                        id: documentID(folderID: folder.id, relativePath: candidate.relativePath),
                        folderID: folder.id, relativePath: candidate.relativePath,
                        title: candidate.components.last!
                    )
                    try write(bytes, named: document.snapshotName, in: corpusFD)
                    budget.bytes += bytes.count
                    documents.append(document)
                }
            }
        }
        guard !documents.isEmpty else {
            throw FindletError.message("No eligible local UTF-8 Markdown or text files were found in the selected folders.")
        }
        try Task.checkCancellation()
        let currentGeneration = try SourceFileAccess.openAbsoluteDirectory(generationURL)
        defer { Darwin.close(currentGeneration) }
        guard SourceFileAccess.sameObject(generationInfo, try SourceFileAccess.information(currentGeneration)),
              SourceFileAccess.sameObject(corpusInfo, try SourceFileAccess.entryInformation(in: currentGeneration, name: "corpus")) else {
            throw FindletError.message("The new corpus folder changed during creation. No replacement index was published.")
        }
        return IndexManifest(generation: generation, documents: documents, folders: folders)
    }

    static func sourceURL(for document: IndexedDocument, in manifest: IndexManifest) throws -> URL {
        try Task.checkCancellation()
        guard manifest.version == 1, manifest.documents.count <= maximumDocuments,
              manifest.documents.filter({ $0.id == document.id }).count == 1,
              manifest.documents.contains(document),
              manifest.folders.filter({ $0.id == document.folderID }).count == 1,
              let folder = manifest.folders.first(where: { $0.id == document.folderID }) else {
            throw FindletError.message("This search result does not belong to the current index.")
        }
        let components = document.relativePath.split(separator: "/", omittingEmptySubsequences: false).map(String.init)
        try SourceFileAccess.validate(components: components)
        guard components.count <= maximumDepth + 1 else {
            throw FindletError.message("This result exceeds the supported relative-path depth.")
        }
        guard let name = components.last, isSupported(name) else {
            throw FindletError.message("This search result is not a supported source document.")
        }
        return try SourceFileAccess.withRoot(folder) { root in
            try SourceFileAccess.withRegularFile(root: root, components: components) { _, _, url in url }
        }
    }

    private static func walk(root: SourceFileAccess.Root, descriptor: Int32, components: [String],
                             budget: Budget, candidates: inout [Candidate]) throws {
        try Task.checkCancellation()
        try SourceFileAccess.forEachEntry(in: descriptor) { name in
            budget.visited += 1
            guard budget.visited <= maximumEntries else {
                throw FindletError.message("The selected folders exceed 100,000 entries. Choose narrower folders and rebuild.")
            }
            if name.hasPrefix(".") { return }
            let info = try SourceFileAccess.entryInformation(in: descriptor, name: name)
            if SourceFileAccess.isExcludedByFlags(info) { return }
            let path = components + [name]
            let directory = SourceFileAccess.isDirectory(info)
            guard directory || (SourceFileAccess.isRegular(info) && isSupported(name)) else { return }
            let url = path.reduce(root.url) { $0.appendingPathComponent($1) }
            guard try SourceFileAccess.isEligible(url: url, info: info, directory: directory) else { return }
            if directory {
                guard path.count <= maximumDepth else {
                    throw FindletError.message("A selected folder exceeds 64 directory levels. Choose a narrower folder and rebuild.")
                }
                let child = try SourceFileAccess.openDirectory(in: descriptor, name: name, expected: info)
                defer { Darwin.close(child) }
                try walk(root: root, descriptor: child, components: path, budget: budget, candidates: &candidates)
            } else {
                guard info.st_size >= 0, info.st_size <= maximumDocumentBytes else {
                    throw FindletError.message("An eligible text file exceeds 2 MiB. Choose a narrower folder or reduce that file before rebuilding.")
                }
                budget.documents += 1
                guard budget.documents <= maximumDocuments else {
                    throw FindletError.message("The selected folders exceed 2,000 text documents. Choose narrower folders and rebuild.")
                }
                candidates.append(Candidate(components: path, info: info))
            }
        }
    }

    private static func read(_ candidate: Candidate, root: SourceFileAccess.Root, budget: Budget) throws -> Data {
        try SourceFileAccess.withRegularFile(root: root, components: candidate.components, expected: candidate.info) { descriptor, before, _ in
            var data = Data()
            data.reserveCapacity(Int(before.st_size))
            var buffer = [UInt8](repeating: 0, count: 64 * 1_024)
            while true {
                try Task.checkCancellation()
                let requested = min(buffer.count, maximumDocumentBytes + 1 - data.count)
                let count = buffer.withUnsafeMutableBytes { Darwin.read(descriptor, $0.baseAddress, requested) }
                if count < 0 {
                    if errno == EINTR { continue }
                    throw SourceFileAccess.readFailure()
                }
                if count == 0 { break }
                guard data.count + count <= maximumDocumentBytes else {
                    throw FindletError.message("An eligible text file exceeds 2 MiB. No replacement index was published.")
                }
                guard budget.bytes + data.count + count <= maximumCombinedBytes else {
                    throw FindletError.message("The selected text files exceed 100 MiB combined. Choose narrower folders and rebuild.")
                }
                data.append(contentsOf: buffer.prefix(count))
            }
            let after = try SourceFileAccess.information(descriptor)
            guard SourceFileAccess.unchanged(before, after), Int64(data.count) == after.st_size else {
                throw SourceFileAccess.changedFailure()
            }
            return data
        }
    }

    private static func write(_ data: Data, named name: String, in corpusFD: Int32) throws {
        let descriptor = name.withCString {
            Darwin.openat(corpusFD, $0, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, mode_t(0o600))
        }
        guard descriptor >= 0 else {
            throw FindletError.message("A private corpus snapshot could not be created. The previous index is retained.")
        }
        defer { Darwin.close(descriptor) }
        try data.withUnsafeBytes { bytes in
            var offset = 0
            while offset < bytes.count {
                try Task.checkCancellation()
                let count = Darwin.write(descriptor, bytes.baseAddress!.advanced(by: offset), min(64 * 1_024, bytes.count - offset))
                if count < 0 && errno == EINTR { continue }
                guard count > 0 else {
                    throw FindletError.message("A corpus snapshot could not be written. The previous index is retained.")
                }
                offset += count
            }
        }
        guard Darwin.fsync(descriptor) == 0 else {
            throw FindletError.message("A corpus snapshot could not be finished. The previous index is retained.")
        }
    }

    private static func isSupported(_ name: String) -> Bool {
        extensions.contains((name as NSString).pathExtension.lowercased())
    }

    // ECMAScript trim whitespace, including BOM, matches QMD's empty-content check.
    private static let qmdWhitespace = CharacterSet(charactersIn:
        "\u{0009}\u{000A}\u{000B}\u{000C}\u{000D}\u{0020}\u{00A0}\u{1680}" +
        "\u{2000}\u{2001}\u{2002}\u{2003}\u{2004}\u{2005}\u{2006}\u{2007}\u{2008}\u{2009}\u{200A}" +
        "\u{2028}\u{2029}\u{202F}\u{205F}\u{3000}\u{FEFF}")

    private static func documentID(folderID: UUID, relativePath: String) -> UUID {
        var bytes = Array(SHA256.hash(data: Data((folderID.uuidString.lowercased() + "\0" + relativePath).utf8)).prefix(16))
        bytes[6] = (bytes[6] & 0x0f) | 0x80
        bytes[8] = (bytes[8] & 0x3f) | 0x80
        return UUID(uuid: (bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7],
                           bytes[8], bytes[9], bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15]))
    }
}
