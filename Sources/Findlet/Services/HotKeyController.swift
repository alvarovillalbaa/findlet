import Foundation
import Carbon
import FindletCore

@MainActor
final class HotKeyController {
    private var registration: EventHotKeyRef?
    private var handler: EventHandlerRef?
    var action: (() -> Void)?
    private let signature: OSType = 0x464C4554 // FLET, an in-process event signature.

    func configure(_ choice: ShortcutChoice) -> String? {
        shutdown()
        guard choice != .disabled else { return nil }
        var event = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        let installed = InstallEventHandler(GetApplicationEventTarget(), { _, event, userData in
            guard let event, let userData else { return OSStatus(eventNotHandledErr) }
            var identifier = EventHotKeyID()
            let status = GetEventParameter(event, EventParamName(kEventParamDirectObject), EventParamType(typeEventHotKeyID),
                                          nil, ByteCount(MemoryLayout<EventHotKeyID>.size), nil, &identifier)
            guard status == noErr, identifier.signature == 0x464C4554, identifier.id == 1 else { return OSStatus(eventNotHandledErr) }
            let controller = Unmanaged<HotKeyController>.fromOpaque(userData).takeUnretainedValue()
            Task { @MainActor in controller.action?() }
            return noErr
        }, 1, &event, Unmanaged.passUnretained(self).toOpaque(), &handler)
        guard installed == noErr else {
            shutdown()
            return "The global shortcut could not be registered. Findlet is still available from the menu bar."
        }
        let modifiers = UInt32(controlKey | (choice == .controlOptionSpace ? optionKey : shiftKey))
        let status = RegisterEventHotKey(UInt32(kVK_Space), modifiers, EventHotKeyID(signature: signature, id: 1),
                                        GetApplicationEventTarget(), OptionBits(kEventHotKeyExclusive), &registration)
        guard status == noErr else {
            shutdown()
            return "That shortcut is unavailable. Choose another in Settings, or open Findlet from the menu bar."
        }
        return nil
    }

    func shutdown() {
        if let registration { UnregisterEventHotKey(registration) }
        if let handler { RemoveEventHandler(handler) }
        registration = nil
        handler = nil
    }
}
