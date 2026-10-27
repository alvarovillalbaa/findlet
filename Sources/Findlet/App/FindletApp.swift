import AppKit
import SwiftUI

@main
@MainActor
struct FindletApp: App {
    @NSApplicationDelegateAdaptor(FindletAppDelegate.self) private var appDelegate

    var body: some Scene {
        MenuBarExtra("Findlet", systemImage: "doc.text.magnifyingglass") {
            FindletMenuView(model: appDelegate.model, panel: appDelegate.panel)
        }
        Settings {
            FindletSettingsView(model: appDelegate.model)
        }
    }
}

@MainActor
final class FindletAppDelegate: NSObject, NSApplicationDelegate {
    let model: FindletModel
    let panel: SearchPanelController
    private let hotKey = HotKeyController()

    override init() {
        let root = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("com.alvarovillalbaa.Findlet", isDirectory: true)
        let model = FindletModel(applicationSupport: root)
        self.model = model
        panel = SearchPanelController(model: model)
        super.init()
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        hotKey.action = { [weak self] in self?.panel.toggle() }
        model.shortcutChanged = { [weak self] shortcut in
            guard let self else { return }
            self.model.shortcutNotice = self.hotKey.configure(shortcut)
        }
        model.shortcutNotice = hotKey.configure(model.settings.shortcut)
        Task {
            await model.initialize()
            if model.needsSetup || model.needsRebuild { panel.show() }
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if model.prepareToQuitIfIdle() { return .terminateNow }
        let alert = NSAlert()
        alert.messageText = "Wait for Findlet's current operation before quitting."
        alert.informativeText = "Cancel and keep Findlet open while its owned process exits. Original files are never removed."
        alert.addButton(withTitle: "Cancel and Stay")
        alert.addButton(withTitle: "Keep Waiting")
        if alert.runModal() == .alertFirstButtonReturn { Task { await model.cancel() } }
        return .terminateCancel
    }

    func applicationWillTerminate(_ notification: Notification) { hotKey.shutdown() }
}
