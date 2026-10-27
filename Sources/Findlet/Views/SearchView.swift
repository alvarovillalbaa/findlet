import AppKit
import SwiftUI
import FindletCore

@MainActor
struct SearchView: View {
    @Bindable var model: FindletModel
    let dismiss: () -> Void
    @Environment(\.openSettings) private var openSettings

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "doc.text.magnifyingglass").font(.title2)
                Text("Findlet").font(.headline)
                Spacer()
                Button { showSettings() } label: { Image(systemName: "gearshape") }
                    .help("Open Settings")
                    .accessibilityLabel("Open Settings")
                Button(action: dismiss) { Image(systemName: "xmark") }
                    .help("Dismiss search")
                    .accessibilityLabel("Dismiss search")
            }
            SearchInput(text: $model.query, focusRequest: model.focusRequest,
                        disabled: model.isCancelling || (model.isBusy && model.operation != .searching),
                        changed: model.queryChanged, move: model.moveSelection,
                        submit: { model.openSelected() }, dismiss: dismiss)
                .frame(height: 32)
            Picker("Search mode", selection: $model.mode) {
                ForEach(SearchMode.allCases) { mode in Text(mode.title).tag(mode) }
            }
            .pickerStyle(.segmented)
            .disabled(model.isCancelling || (model.isBusy && model.operation != .searching))
            .onChange(of: model.mode) { _, _ in model.queryChanged() }
            if let error = model.settingsReadError {
                state("Settings need attention", symbol: "exclamationmark.triangle", message: error)
                HStack {
                    Button("Reload Settings") { model.retrySettings() }.disabled(model.isBusy)
                    Button("Show Settings File") { NSWorkspace.shared.activateFileViewerSelecting([model.settingsURL]) }
                }
            } else if model.needsSetup {
                state("Choose what to search", symbol: "folder.badge.plus",
                      message: "Select Markdown or text folders, an existing Node executable, and QMD 2.8.3 in Settings. Nothing is indexed automatically.")
                Button("Set Up Findlet…") { showSettings() }.buttonStyle(.borderedProminent)
            } else if model.needsRebuild {
                state("Rebuild to use this setup", symbol: "arrow.triangle.2.circlepath",
                      message: "Your folder or runtime selection has changed, or no index is ready. Original documents remain unchanged.")
                Button("Rebuild Local Index") { model.rebuild() }
                    .disabled(!model.canRebuild)
                    .buttonStyle(.borderedProminent)
            } else if model.mode.needsModels && !model.semanticReady {
                state("Prepare semantic search explicitly", symbol: "sparkle.magnifyingglass",
                      message: "Choose three existing local GGUF files, rebuild for the updated runtime, then accept and run CPU preparation in Settings. Findlet does not download models.")
                Button("Open Semantic Settings…") { showSettings() }
            } else if model.query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                state("Search your local documents", symbol: "magnifyingglass",
                      message: "Type a query. Use ↑ and ↓ to select a result, Return to open it, or Escape to dismiss.")
            } else if model.hits.isEmpty {
                state(model.completedQuery == nil ? "Waiting for results" : "No matching documents",
                      symbol: "doc.text.magnifyingglass",
                      message: model.completedQuery == nil ? "Search starts after you pause typing." : "Try different words or another prepared search mode.")
            } else {
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 5) {
                            ForEach(model.hits) { hit in
                                resultRow(hit).id(hit.id)
                            }
                        }
                    }
                    .onChange(of: model.selectedID) { _, selected in
                        if let selected { proxy.scrollTo(selected, anchor: .center) }
                    }
                }
                HStack {
                    Button("Open") { model.openSelected() }
                    Button("Reveal in Finder") { model.openSelected(reveal: true) }
                    Spacer()
                    Text("\(model.hits.count) results").foregroundStyle(.secondary)
                }
                .disabled(model.isBusy || model.selectedHit == nil)
            }
            Spacer(minLength: 0)
            if let error = model.errorMessage {
                Label(error, systemImage: "exclamationmark.triangle")
                    .font(.callout).foregroundStyle(.primary).lineLimit(4).textSelection(.enabled)
            }
            if let notice = model.notice {
                Text(notice).font(.caption).foregroundStyle(.secondary)
            }
            if let shortcutNotice = model.shortcutNotice {
                Text(shortcutNotice).font(.caption).foregroundStyle(.secondary)
            }
            Divider()
            HStack(spacing: 8) {
                if model.isBusy {
                    ProgressView().controlSize(.small)
                    Text(model.isCancelling ? "Cancelling; waiting for the process to exit…" : model.operation.title)
                    Spacer()
                    Button("Cancel") { Task { await model.cancel() } }.disabled(model.isCancelling)
                } else {
                    Text("Local · QMD 2.8.3 · \(model.summary.documentCount) indexed documents")
                    Spacer()
                    Text(model.settings.shortcut.title)
                }
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(18)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(.regularMaterial)
    }

    private func showSettings() { NSApp.activate(ignoringOtherApps: true); openSettings() }

    private func state(_ title: String, symbol: String, message: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: symbol).font(.headline)
            Text(message).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
        }
        .padding(.vertical, 12)
    }

    private func resultRow(_ hit: SearchHit) -> some View {
        Button { model.select(hit) } label: {
            VStack(alignment: .leading, spacing: 4) {
                Text(hit.title).font(.headline).lineLimit(1)
                Text(hit.path + (hit.line > 0 ? " · line \(hit.line)" : ""))
                    .font(.caption).foregroundStyle(.secondary).lineLimit(1)
                Text(hit.snippet).font(.callout).foregroundStyle(.secondary).lineLimit(2)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(10)
            .background(model.selectedID == hit.id ? Color.accentColor.opacity(0.15) : Color.clear,
                        in: RoundedRectangle(cornerRadius: 8))
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .simultaneousGesture(TapGesture(count: 2).onEnded { model.select(hit); model.openSelected() })
        .accessibilityLabel(hit.title + ". " + hit.path)
        .accessibilityAddTraits(model.selectedID == hit.id ? .isSelected : [])
    }
}

private struct SearchInput: NSViewRepresentable {
    @Binding var text: String
    let focusRequest: Int
    let disabled: Bool
    let changed: () -> Void
    let move: (Int) -> Void
    let submit: () -> Void
    let dismiss: () -> Void

    func makeCoordinator() -> Coordinator { Coordinator(self) }
    func makeNSView(context: Context) -> NSSearchField {
        let field = NSSearchField()
        field.placeholderString = "Search selected documents"
        field.setAccessibilityLabel("Search selected documents")
        field.sendsSearchStringImmediately = true
        field.delegate = context.coordinator
        return field
    }
    func updateNSView(_ field: NSSearchField, context: Context) {
        context.coordinator.parent = self
        if field.stringValue != text { field.stringValue = text }
        field.isEnabled = !disabled
        if context.coordinator.focusRequest != focusRequest {
            context.coordinator.focusRequest = focusRequest
            DispatchQueue.main.async { if field.isEnabled { field.window?.makeFirstResponder(field) } }
        }
    }
    final class Coordinator: NSObject, NSSearchFieldDelegate {
        var parent: SearchInput
        var focusRequest = -1
        init(_ parent: SearchInput) { self.parent = parent }
        func controlTextDidChange(_ notification: Notification) {
            guard let field = notification.object as? NSSearchField else { return }
            parent.text = field.stringValue
            parent.changed()
        }
        func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
            guard !textView.hasMarkedText() else { return false }
            if commandSelector == #selector(NSResponder.moveDown(_:)) { parent.move(1); return true }
            if commandSelector == #selector(NSResponder.moveUp(_:)) { parent.move(-1); return true }
            if commandSelector == #selector(NSResponder.insertNewline(_:)) { parent.submit(); return true }
            if commandSelector == #selector(NSResponder.cancelOperation(_:)) { parent.dismiss(); return true }
            return false
        }
    }
}
