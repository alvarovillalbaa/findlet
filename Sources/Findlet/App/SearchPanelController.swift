import AppKit
import SwiftUI

private final class SearchPanel: NSPanel {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }
}

@MainActor
final class SearchPanelController: NSObject, NSWindowDelegate {
    private let model: FindletModel
    private var panel: SearchPanel?

    init(model: FindletModel) { self.model = model }

    func toggle() {
        if panel?.isVisible == true { hide() } else { show() }
    }

    func show() {
        if panel == nil {
            let panel = SearchPanel(contentRect: NSRect(x: 0, y: 0, width: 690, height: 510),
                                    styleMask: [.titled, .fullSizeContentView, .nonactivatingPanel],
                                    backing: .buffered, defer: false)
            panel.title = "Findlet Search"
            panel.titleVisibility = .hidden
            panel.titlebarAppearsTransparent = true
            panel.isMovableByWindowBackground = true
            panel.isReleasedWhenClosed = false
            panel.hidesOnDeactivate = false
            panel.level = .floating
            panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
            panel.delegate = self
            let hosting = NSHostingView(rootView: SearchView(model: model, dismiss: { [weak self] in self?.hide() }))
            // The panel owns its screen-bounded frame; intrinsic SwiftUI bounds
            // must not enlarge the window and push result actions off screen.
            hosting.sizingOptions = []
            panel.contentView = hosting
            self.panel = panel
        }
        guard let panel else { return }
        let screen = NSScreen.screens.first { NSMouseInRect(NSEvent.mouseLocation, $0.frame, false) } ?? NSScreen.main
        if let visible = screen?.visibleFrame {
            let width = min(690, max(320, visible.width - 40))
            let height = min(510, max(280, visible.height - 40))
            panel.setFrame(NSRect(x: visible.midX - width / 2,
                                  y: visible.maxY - height - min(90, (visible.height - height) / 2),
                                  width: width, height: height), display: false)
        }
        panel.makeKeyAndOrderFront(nil)
        model.focusSearch()
    }

    func hide() { panel?.orderOut(nil) }
    func windowDidResignKey(_ notification: Notification) { hide() }
}
