import Foundation

public enum SearchMode: String, CaseIterable, Codable, Identifiable, Sendable {
    case keyword, semantic, hybrid
    public var id: String { rawValue }
    public var title: String {
        switch self { case .keyword: return "Keyword"; case .semantic: return "Semantic"; case .hybrid: return "Hybrid" }
    }
    public var command: String {
        switch self { case .keyword: return "search"; case .semantic: return "vsearch"; case .hybrid: return "query" }
    }
    public var needsModels: Bool { self != .keyword }
}

public struct FolderSelection: Codable, Identifiable, Equatable, Sendable {
    public var id: UUID
    public var name: String
    public var bookmark: Data
    public init(id: UUID = UUID(), name: String, bookmark: Data) {
        self.id = id; self.name = name; self.bookmark = bookmark
    }
}

public struct IndexedDocument: Codable, Identifiable, Equatable, Sendable {
    public var id: UUID
    public var folderID: UUID
    public var relativePath: String
    public var title: String
    public var snapshotName: String { id.uuidString.lowercased() + ".md" }
    public init(id: UUID = UUID(), folderID: UUID, relativePath: String, title: String) {
        self.id = id; self.folderID = folderID; self.relativePath = relativePath; self.title = title
    }
}

public struct IndexManifest: Codable, Sendable {
    public var version: Int = 1
    public var generation: UUID
    public var createdAt: Date
    public var documents: [IndexedDocument]
    public var folders: [FolderSelection]
    public var embeddingReady: Bool = false
    public init(generation: UUID, documents: [IndexedDocument], folders: [FolderSelection]) {
        self.generation = generation; self.createdAt = Date(); self.documents = documents; self.folders = folders
    }
}

public struct SearchHit: Identifiable, Equatable, Sendable {
    public var id: UUID { documentID }
    public var documentID: UUID
    public var title: String
    public var path: String
    public var snippet: String
    public var line: Int
    public var score: Double
    public init(documentID: UUID, title: String, path: String, snippet: String, line: Int, score: Double) {
        self.documentID = documentID; self.title = title; self.path = path
        self.snippet = snippet; self.line = line; self.score = score
    }
}

public struct RuntimeConfiguration: Codable, Equatable, Sendable {
    public var nodePath: String = ""
    public var qmdPackagePath: String = ""
    public var embeddingModelPath: String = ""
    public var expansionModelPath: String = ""
    public var rerankerModelPath: String = ""
    public var modelPreparationAccepted: Bool = false
    public init() {}
}

public enum ShortcutChoice: String, CaseIterable, Codable, Identifiable, Sendable {
    case controlOptionSpace, controlShiftSpace, disabled
    public var id: String { rawValue }
    public var title: String {
        switch self {
        case .controlOptionSpace: return "⌃⌥Space"
        case .controlShiftSpace: return "⌃⇧Space"
        case .disabled: return "Disabled"
        }
    }
}

public struct FindletSettings: Codable, Sendable {
    public var folders: [FolderSelection] = []
    public var runtime = RuntimeConfiguration()
    public var shortcut: ShortcutChoice = .controlOptionSpace
    public init() {}
}

public struct IndexSummary: Sendable {
    public var documentCount: Int
    public var updatedAt: Date?
    public var embeddingReady: Bool
    public init(documentCount: Int = 0, updatedAt: Date? = nil, embeddingReady: Bool = false) {
        self.documentCount = documentCount; self.updatedAt = updatedAt; self.embeddingReady = embeddingReady
    }
}

public enum FindletError: LocalizedError {
    case message(String)
    public var errorDescription: String? {
        switch self { case .message(let message): return message }
    }
}
