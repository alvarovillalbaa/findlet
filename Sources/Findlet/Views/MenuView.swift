import AppKit
import SwiftUI

@MainActor
struct FindletMenuView: View {
    let model: FindletModel
    let panel: SearchPanelController
    @Environment(\.openSettings) private var openSettings

    var body: some View {
        Button("Search…") { panel.show() }
        Button("Settings…") { NSApp.activate(ignoringOtherApps: true); openSettings() }
        Divider()
        Text("\(model.summary.documentCount) indexed documents")
        if model.isBusy {
            Text(model.isCancelling ? "Cancelling; waiting for exit…" : model.operation.title)
            Button("Cancel Operation") { Task { await model.cancel() } }.disabled(model.isCancelling)
        } else {
            Button("Rebuild Local Index") { model.rebuild() }.disabled(!model.canRebuild)
            Button("Prepare Semantic Search") { model.prepareSemantic() }.disabled(!model.canPrepare)
        }
        Divider()
        Button("Quit Findlet") { NSApp.terminate(nil) }
    }
}
