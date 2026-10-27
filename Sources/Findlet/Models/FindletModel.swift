import AppKit
import Foundation
import Observation
import FindletCore

enum FindletOperation: Equatable {
    case idle, loading, searching, rebuilding, preparing, forgetting, opening
    var title: String {
        switch self {
        case .idle: "Ready"
        case .loading: "Reading index status…"
        case .searching: "Searching…"
        case .rebuilding: "Building a new local index…"
        case .preparing: "Preparing local CPU semantic search…"
        case .forgetting: "Removing Findlet's index…"
        case .opening: "Checking the original file…"
        }
    }
}

enum RuntimePathChoice: Equatable {
    case node, package, embedding, expansion, reranker
}

@MainActor @Observable
final class FindletModel {
    var query = ""
    var mode: SearchMode = .keyword
    private(set) var hits: [SearchHit] = []
    private(set) var selectedID: UUID?
    private(set) var completedQuery: String?
    private(set) var settings = FindletSettings()
    private(set) var summary = IndexSummary()
    private(set) var operation: FindletOperation = .idle
    private(set) var isCancelling = false
    private(set) var errorMessage: String?
    private(set) var notice: String?
    private(set) var settingsReadError: String?
    var shortcutNotice: String?
    private(set) var focusRequest = 0
    @ObservationIgnored var shortcutChanged: ((ShortcutChoice) -> Void)?
    @ObservationIgnored private let store: SettingsStore
    @ObservationIgnored private let engine: FindletEngine
    @ObservationIgnored private var setup = StoredFindletSetup()
    @ObservationIgnored private var initialized = false
    @ObservationIgnored private var queryGeneration = 0
    @ObservationIgnored private var debounce: Task<Void, Never>?
    @ObservationIgnored private var work: Task<Void, Never>?
    @ObservationIgnored private var workID: UUID?

    init(applicationSupport: URL) {
        store = SettingsStore(applicationSupport: applicationSupport)
        engine = FindletEngine(applicationSupport: applicationSupport)
        loadSettings()
    }

    var settingsURL: URL { store.url }
    var isBusy: Bool { operation != .idle || isCancelling }
    var hasRuntime: Bool { !settings.runtime.nodePath.isEmpty && !settings.runtime.qmdPackagePath.isEmpty }
    var needsSetup: Bool { settingsReadError != nil || !hasRuntime || settings.folders.isEmpty }
    var needsRebuild: Bool {
        setup.indexedFolders != settings.folders
            || setup.indexedRuntime.map(runtimeIdentity) != runtimeIdentity(settings.runtime)
            || summary.updatedAt == nil
    }
    var semanticReady: Bool {
        settings.runtime.modelPreparationAccepted && !needsRebuild && summary.embeddingReady
            && setup.preparedRuntime.map(runtimeIdentity) == runtimeIdentity(settings.runtime)
    }
    var hasModels: Bool {
        let runtime = settings.runtime
        return !runtime.embeddingModelPath.isEmpty && !runtime.expansionModelPath.isEmpty && !runtime.rerankerModelPath.isEmpty
    }
    var canRebuild: Bool { !isBusy && !needsSetup }
    var canPrepare: Bool { !isBusy && !needsSetup && !needsRebuild && hasModels && settings.runtime.modelPreparationAccepted }
    var selectedHit: SearchHit? { hits.first { $0.id == selectedID } }

    func initialize() async {
        guard !initialized else { return }
        initialized = true
        operation = .loading
        defer { operation = .idle }
        do { summary = try await engine.summary() }
        catch { errorMessage = "The local index status could not be read. No rebuild was started." }
    }

    func focusSearch() { focusRequest += 1 }

    func retrySettings() {
        guard !isBusy else { return }
        invalidateQuery()
        loadSettings()
        shortcutChanged?(settings.shortcut)
        notice = settingsReadError == nil ? "Settings were reloaded. Rebuild explicitly if the setup changed." : nil
    }

    private func loadSettings() {
        do {
            setup = try store.load()
            settings = setup.settings
            settingsReadError = nil
        } catch {
            settingsReadError = error.localizedDescription
            errorMessage = nil
        }
    }

    func chooseFolders(replacing replacementID: UUID? = nil) {
        guard !isBusy, settingsReadError == nil else { return }
        let panel = NSOpenPanel()
        panel.title = "Choose folders to search"
        panel.message = "Findlet reads local Markdown and text files only after you explicitly rebuild. Original files are never edited."
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = replacementID == nil
        guard panel.runModal() == .OK else { return }
        do {
            var folders = settings.folders
            var existing: [URL: Int] = [:]
            for (index, folder) in folders.enumerated() {
                var stale = false
                if let url = try? URL(resolvingBookmarkData: folder.bookmark, options: [.withoutUI, .withoutMounting],
                                      relativeTo: nil, bookmarkDataIsStale: &stale) {
                    existing[url.standardizedFileURL] = index
                }
            }
            for url in panel.urls {
                let values = try url.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])
                guard values.isDirectory == true, values.isSymbolicLink != true else {
                    throw FindletError.message("Choose regular local folders rather than symbolic links.")
                }
                let bookmark = try url.bookmarkData(options: [], includingResourceValuesForKeys: nil, relativeTo: nil)
                let replacement = replacementID.flatMap { id in folders.firstIndex { $0.id == id } }
                    ?? existing[url.standardizedFileURL]
                if let replacement {
                    folders[replacement] = FolderSelection(id: folders[replacement].id,
                        name: String(url.lastPathComponent.prefix(200)), bookmark: bookmark)
                } else {
                    existing[url.standardizedFileURL] = folders.count
                    folders.append(FolderSelection(name: String(url.lastPathComponent.prefix(200)), bookmark: bookmark))
                }
            }
            var next = settings
            next.folders = folders
            try saveSettings(next)
        } catch { errorMessage = error.localizedDescription }
    }

    func removeFolder(_ id: UUID) {
        guard !isBusy else { return }
        var next = settings
        next.folders.removeAll { $0.id == id }
        do { try saveSettings(next) } catch { errorMessage = error.localizedDescription }
    }

    func choosePath(_ choice: RuntimePathChoice) {
        guard !isBusy, settingsReadError == nil else { return }
        let panel = NSOpenPanel()
        panel.canChooseDirectories = choice == .package
        panel.canChooseFiles = choice != .package
        panel.allowsMultipleSelection = false
        panel.title = choice == .node ? "Choose an existing Node executable" : choice == .package ? "Choose the QMD 2.8.3 package folder" : "Choose an existing local GGUF model"
        panel.message = "Findlet does not install runtimes, packages or models. Selecting a path does not run it."
        guard panel.runModal() == .OK, let url = panel.url else { return }
        if choice == .node && !FileManager.default.isExecutableFile(atPath: url.path) {
            errorMessage = "Choose an existing executable Node file."; return
        }
        if choice != .node && choice != .package && url.pathExtension.lowercased() != "gguf" {
            errorMessage = "Choose an existing .gguf model file."; return
        }
        var next = settings
        switch choice {
        case .node: next.runtime.nodePath = url.path
        case .package: next.runtime.qmdPackagePath = url.path
        case .embedding: next.runtime.embeddingModelPath = url.path
        case .expansion: next.runtime.expansionModelPath = url.path
        case .reranker: next.runtime.rerankerModelPath = url.path
        }
        next.runtime.modelPreparationAccepted = false
        do { try saveSettings(next) } catch { errorMessage = error.localizedDescription }
    }

    func setShortcut(_ choice: ShortcutChoice) {
        guard !isBusy else { return }
        var next = settings; next.shortcut = choice
        do { try saveSettings(next); shortcutChanged?(choice) }
        catch { errorMessage = error.localizedDescription }
    }

    func setPreparationAccepted(_ accepted: Bool) {
        guard !isBusy else { return }
        var next = settings; next.runtime.modelPreparationAccepted = accepted
        do { try saveSettings(next) } catch { errorMessage = error.localizedDescription }
    }

    private func saveSettings(_ next: FindletSettings) throws {
        guard settingsReadError == nil else { throw FindletError.message("Reload or repair the original settings before making changes.") }
        var candidate = setup
        candidate.settings = next
        try store.save(candidate)
        let changed = next.folders != settings.folders || runtimeIdentity(next.runtime) != runtimeIdentity(settings.runtime)
        let consentChanged = next.runtime.modelPreparationAccepted != settings.runtime.modelPreparationAccepted
        setup = candidate
        settings = next
        if changed {
            invalidateQuery()
            summary = IndexSummary(documentCount: summary.documentCount, updatedAt: summary.updatedAt, embeddingReady: false)
            notice = "Setup changed. Rebuild the keyword index, then explicitly prepare semantic search if needed."
        } else if consentChanged {
            invalidateQuery()
        }
    }

    func rebuild() {
        guard canRebuild else { return }
        invalidateQuery()
        let folders = settings.folders
        let runtime = settings.runtime
        begin(.rebuilding) { model in
            let summary = try await model.engine.rebuild(folders: folders, runtime: runtime)
            model.summary = summary
            model.setup.indexedFolders = folders
            model.setup.indexedRuntime = runtimeIdentity(runtime)
            model.setup.preparedRuntime = nil
            model.persistMetadata()
            model.notice = "Indexed \(summary.documentCount) local documents. Type a query to search."
        }
    }

    func prepareSemantic() {
        guard canPrepare else { return }
        invalidateQuery()
        let runtime = settings.runtime
        begin(.preparing) { model in
            model.summary = try await model.engine.prepareSemantic(runtime: runtime)
            model.setup.preparedRuntime = runtimeIdentity(runtime)
            model.persistMetadata()
            model.notice = "Local semantic preparation finished. Semantic and Hybrid searches are now available."
        }
    }

    func forgetIndex() {
        guard !isBusy, settingsReadError == nil else { return }
        invalidateQuery()
        begin(.forgetting) { model in
            try await model.engine.forgetIndex()
            model.summary = IndexSummary()
            model.setup.indexedFolders = nil
            model.setup.indexedRuntime = nil
            model.setup.preparedRuntime = nil
            model.persistMetadata()
            model.notice = "Findlet's generated index was removed. Original folders, runtimes and model files were retained."
        }
    }

    private func persistMetadata() {
        do { try store.save(setup) }
        catch { errorMessage = "The operation finished, but its setup status could not be saved. Keep this window open; reload may require another rebuild." }
    }

    func queryChanged() {
        queryGeneration += 1
        let generation = queryGeneration
        debounce?.cancel()
        hits = []; selectedID = nil
        completedQuery = nil
        errorMessage = nil
        guard operation == .idle || operation == .searching else { return }
        let oldWork = operation == .searching ? work : nil
        oldWork?.cancel()
        debounce = Task { [weak self] in
            guard let self, !Task.isCancelled else { return }
            if let oldWork {
                await self.engine.cancel()
                await oldWork.value
            }
            do { try await Task.sleep(nanoseconds: 250_000_000) } catch { return }
            guard !Task.isCancelled, self.queryGeneration == generation, !self.isBusy else { return }
            let query = self.query.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !query.isEmpty else { return }
            guard query.utf8.count <= 4096 else { self.errorMessage = "Use a query of up to 4,096 UTF-8 bytes."; return }
            guard !self.needsSetup, !self.needsRebuild else { return }
            guard !self.mode.needsModels || self.semanticReady else { return }
            let mode = self.mode
            let runtime = self.settings.runtime
            self.begin(.searching) { model in
                let results = try await model.engine.search(query, mode: mode, runtime: runtime)
                guard !Task.isCancelled, model.queryGeneration == generation else { return }
                model.hits = results
                model.selectedID = results.first?.id
                model.completedQuery = query
            }
        }
    }

    func select(_ hit: SearchHit) { selectedID = hit.id }

    func moveSelection(_ direction: Int) {
        guard !hits.isEmpty else { return }
        let index = selectedID.flatMap { selected in hits.firstIndex { $0.id == selected } } ?? 0
        selectedID = hits[min(hits.count - 1, max(0, index + direction))].id
    }

    func openSelected(reveal: Bool = false) {
        guard !isBusy, let hit = selectedHit, !needsRebuild else { return }
        begin(.opening) { model in
            let url = try await model.engine.sourceURL(for: hit)
            guard !Task.isCancelled, url.isFileURL else { return }
            if reveal { NSWorkspace.shared.activateFileViewerSelecting([url]) }
            else if !NSWorkspace.shared.open(url) {
                throw FindletError.message("The original file could not be opened. Try Reveal in Finder.")
            }
        }
    }

    private func begin(_ operation: FindletOperation, action: @escaping @MainActor (FindletModel) async throws -> Void) {
        guard !isBusy else { return }
        debounce?.cancel()
        let token = UUID()
        let generation = queryGeneration
        workID = token
        self.operation = operation
        errorMessage = nil
        notice = nil
        work = Task { [weak self] in
            guard let self else { return }
            defer {
                if self.workID == token { self.work = nil; self.workID = nil; self.operation = .idle }
            }
            do { try Task.checkCancellation(); try await action(self) }
            catch is CancellationError {
                if self.workID == token && (operation != .searching || self.queryGeneration == generation) {
                    self.notice = "Operation cancelled. Original files were retained."
                }
            }
            catch {
                if self.workID == token && (operation != .searching || self.queryGeneration == generation) {
                    self.errorMessage = error.localizedDescription
                }
            }
        }
    }

    func cancel() async {
        guard !isCancelling else { return }
        queryGeneration += 1
        debounce?.cancel()
        hits = []; selectedID = nil
        completedQuery = nil
        let pending = work
        pending?.cancel()
        isCancelling = true
        await engine.cancel()
        await pending?.value
        isCancelling = false
    }

    func prepareToQuitIfIdle() -> Bool {
        guard !isBusy else { return false }
        // A debounce has no process yet, but must not start one after the quit
        // guard succeeds. Both this check and begin() run on the main actor.
        invalidateQuery()
        return true
    }

    private func invalidateQuery() {
        queryGeneration += 1
        debounce?.cancel()
        hits = []; selectedID = nil
        completedQuery = nil
    }
}
