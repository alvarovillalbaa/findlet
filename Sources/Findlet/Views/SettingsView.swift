import AppKit
import SwiftUI
import FindletCore

@MainActor
struct FindletSettingsView: View {
    @Bindable var model: FindletModel
    @State private var confirmForget = false

    var body: some View {
        Form {
            if let error = model.settingsReadError {
                Section("Settings could not be loaded") {
                    Text(error).textSelection(.enabled)
                    Text("Existing settings will not be overwritten. Repair the file or restore a valid copy, then reload it.")
                    HStack {
                        Button("Show Settings File") { NSWorkspace.shared.activateFileViewerSelecting([model.settingsURL]) }
                        Button("Reload Settings") { model.retrySettings() }.disabled(model.isBusy)
                    }
                }
            }
            Section("Folders") {
                if model.settings.folders.isEmpty { Text("No folders selected.").foregroundStyle(.secondary) }
                ForEach(model.settings.folders) { folder in
                    HStack {
                        Label(folder.name, systemImage: "folder")
                        Spacer()
                        Button("Choose Again…") { model.chooseFolders(replacing: folder.id) }
                            .accessibilityLabel("Choose \(folder.name) again")
                        Button("Remove") { model.removeFolder(folder.id) }
                            .accessibilityLabel("Remove \(folder.name) from search")
                    }
                }
                Button("Add Folders…") { model.chooseFolders() }
                Text("Up to 32 folders. Rebuild reads local UTF-8 .md, .markdown and .txt files into Findlet's private snapshot. Hidden files, symlinks, packages and cloud placeholders are excluded. Originals are never edited.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            .disabled(model.isBusy || model.settingsReadError != nil)
            Section("Existing local runtime") {
                pathRow("Node executable", path: model.settings.runtime.nodePath, choice: .node)
                pathRow("QMD 2.8.3 package", path: model.settings.runtime.qmdPackagePath, choice: .package)
                Text("Select installations already on this Mac. Findlet does not install Node or QMD, and does not use your global QMD index. Changing paths requires a rebuild.")
                    .font(.caption).foregroundStyle(.secondary)
                Button("Rebuild Local Index") { model.rebuild() }.disabled(!model.canRebuild)
            }
            .disabled(model.isBusy || model.settingsReadError != nil)
            Section("Local CPU semantic search") {
                pathRow("Embedding model", path: model.settings.runtime.embeddingModelPath, choice: .embedding)
                pathRow("Expansion model", path: model.settings.runtime.expansionModelPath, choice: .expansion)
                pathRow("Reranker model", path: model.settings.runtime.rerankerModelPath, choice: .reranker)
                Text("Choose three existing local GGUF files. Preparation uses the selected CPU runtime and can consume CPU, memory and disk. A compatible CPU binding must already be installed. Findlet does not install bindings or download models.")
                    .font(.caption).foregroundStyle(.secondary)
                Toggle("I understand and want to prepare these local models", isOn: Binding(
                    get: { model.settings.runtime.modelPreparationAccepted }, set: model.setPreparationAccepted))
                Button(model.semanticReady ? "Prepare Again" : "Prepare Semantic Search") { model.prepareSemantic() }
                    .disabled(!model.canPrepare)
                if model.needsRebuild { Text("Rebuild the index for the current paths before preparation.").font(.caption) }
            }
            .disabled(model.isBusy || model.settingsReadError != nil)
            Section("Shortcut") {
                Picker("Open search", selection: Binding(get: { model.settings.shortcut }, set: model.setShortcut)) {
                    ForEach(ShortcutChoice.allCases) { choice in Text(choice.title).tag(choice) }
                }
                if let message = model.shortcutNotice { Text(message).font(.caption).foregroundStyle(.secondary) }
                Text("The menu-bar icon remains available if another app reserves the shortcut.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            .disabled(model.isBusy || model.settingsReadError != nil)
            Section("Generated index") {
                Text("\(model.summary.documentCount) documents in Findlet's current index.")
                Button("Forget Findlet Index…", role: .destructive) { confirmForget = true }
                    .disabled(model.isBusy || model.settingsReadError != nil)
            }
            if model.isBusy {
                HStack {
                    ProgressView().controlSize(.small)
                    Text(model.isCancelling ? "Cancelling; waiting for exit…" : model.operation.title)
                    Spacer()
                    Button("Cancel") { Task { await model.cancel() } }.disabled(model.isCancelling)
                }
            }
            if let error = model.errorMessage { Text(error).foregroundStyle(.primary).textSelection(.enabled) }
            if let notice = model.notice { Text(notice).foregroundStyle(.secondary) }
        }
        .formStyle(.grouped)
        .frame(width: 620, height: 650)
        .confirmationDialog("Forget Findlet's generated index?", isPresented: $confirmForget, titleVisibility: .visible) {
            Button("Forget Index", role: .destructive) { model.forgetIndex() }
        } message: {
            Text("This removes only Findlet's generated search data. Original folders, settings, Node, QMD and model files are retained.")
        }
    }

    private func pathRow(_ title: String, path: String, choice: RuntimePathChoice) -> some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                Text(path.isEmpty ? "Not selected" : path)
                    .font(.caption).foregroundStyle(.secondary)
                    .lineLimit(2).textSelection(.enabled)
            }
            Spacer()
            Button("Choose…") { model.choosePath(choice) }.accessibilityLabel("Choose \(title.lowercased())")
        }
    }
}
