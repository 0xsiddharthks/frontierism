// Query and change file defaults with macOS's consent-aware API, including dynamic UTIs.
import AppKit
import UniformTypeIdentifiers

@available(macOS 12.0, *)
final class FileHandlers {
    let selectors: [String]
    let application: URL
    let workspace = NSWorkspace.shared
    var errors: [String: String] = [:]

    init(selectors: [String], application: String) {
        self.selectors = selectors
        self.application = URL(fileURLWithPath: application)
    }

    func contentType(_ selector: String) -> UTType? {
        if selector.hasPrefix(".") {
            return UTType(filenameExtension: String(selector.dropFirst()))
        }
        return UTType(selector)
    }

    func current(_ selector: String) -> String? {
        guard let type = contentType(selector),
              let url = workspace.urlForApplication(toOpen: type) else { return nil }
        return Bundle(url: url)?.bundleIdentifier
    }

    func finish() -> Never {
        var handlers: [String: Any] = [:]
        for selector in selectors { handlers[selector] = current(selector) as Any? ?? NSNull() }
        let result: [String: Any] = ["handlers": handlers, "errors": errors]
        let data = try! JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
        FileHandle.standardOutput.write(data)
        exit(errors.isEmpty ? 0 : 1)
    }

    func apply(_ index: Int = 0) {
        guard index < selectors.count else { finish() }
        let selector = selectors[index]
        guard let type = contentType(selector) else {
            errors[selector] = "macOS could not resolve this file type"
            apply(index + 1)
            return
        }
        let desired = Bundle(url: application)?.bundleIdentifier
        if current(selector)?.lowercased() == desired?.lowercased() {
            apply(index + 1)
            return
        }
        workspace.setDefaultApplication(at: application, toOpen: type) { error in
            DispatchQueue.main.async {
                if let error = error { self.errors[selector] = error.localizedDescription }
                self.apply(index + 1)
            }
        }
    }
}

do {
    let data = FileHandle.standardInput.readDataToEndOfFile()
    let request = try JSONSerialization.jsonObject(with: data) as! [String: Any]
    if #available(macOS 12.0, *) {
        let tool = FileHandlers(
            selectors: request["selectors"] as! [String],
            application: request["application"] as! String
        )
        if request["mode"] as? String == "read" { tool.finish() }
        let app = NSApplication.shared
        app.setActivationPolicy(.prohibited)
        tool.apply()
        app.run()
    } else {
        fputs("File defaults require macOS 12 or later.\n", stderr)
        exit(1)
    }
} catch {
    fputs("Invalid file-handler request: \(error)\n", stderr)
    exit(1)
}
