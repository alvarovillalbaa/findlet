import Foundation

public enum QMDContract {
    public static let supportedVersion = "2.8.3"
    public static let collection = "findlet_documents"
    public static let maximumQueryBytes = 4_096
    public static let resultLimit = 20

    public static func searchArguments(query: String, mode: SearchMode) throws -> [String] {
        let text = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, text.utf8.count <= maximumQueryBytes, !text.contains("\0") else {
            throw FindletError.message("Enter a search of 1–4,096 UTF-8 bytes.")
        }
        return ["--index", "findlet", mode.command, "--format", "json", "--full-path",
                "-c", collection, "-n", String(resultLimit), "--", text]
    }

    private struct Row: Decodable {
        let score: Double
        let file: String
        let line: Int?
        let snippet: String?
        let body: String?
    }

    public static func decodeResults(_ data: Data, manifest: IndexManifest, generationURL: URL) throws -> [SearchHit] {
        guard data.count <= 2 * 1_024 * 1_024 else { throw FindletError.message("QMD returned too much output.") }
        let rows = try JSONDecoder().decode([Row].self, from: data)
        guard rows.count <= 200 else { throw FindletError.message("QMD returned too many results.") }
        guard Set(manifest.documents.map(\.id)).count == manifest.documents.count else {
            throw FindletError.message("The document manifest contains duplicate IDs.")
        }
        let corpus = generationURL.appendingPathComponent("corpus", isDirectory: true).standardizedFileURL
        let documents = Dictionary(uniqueKeysWithValues: manifest.documents.map { ($0.snapshotName, $0) })
        var hits: [UUID: SearchHit] = [:]
        for row in rows {
            guard row.score.isFinite, !row.file.contains("\0"), row.file.utf8.count < 16_384,
                  row.file.hasPrefix("/") || row.file.hasPrefix("./") else {
                throw FindletError.message("QMD returned an unsupported result path or score.")
            }
            let file = URL(fileURLWithPath: row.file, relativeTo: generationURL).standardizedFileURL
            guard file.deletingLastPathComponent() == corpus,
                  let document = documents[file.lastPathComponent] else {
                throw FindletError.message("QMD returned a result outside this index.")
            }
            let snippet = row.snippet ?? row.body ?? ""
            guard snippet.utf8.count <= 65_536, (row.line ?? 1) >= 1 else {
                throw FindletError.message("QMD returned an invalid excerpt.")
            }
            let hit = SearchHit(documentID: document.id, title: document.title, path: document.relativePath,
                                snippet: String(snippet.prefix(2_000)), line: row.line ?? 1, score: row.score)
            if hits[document.id].map({ $0.score < hit.score }) ?? true { hits[document.id] = hit }
        }
        return hits.values.sorted {
            if $0.score != $1.score { return $0.score > $1.score }
            return $0.path.localizedStandardCompare($1.path) == .orderedAscending
        }.prefix(resultLimit).map { $0 }
    }
}
