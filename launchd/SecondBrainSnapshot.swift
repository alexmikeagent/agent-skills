import Darwin
import Foundation

let python = URL(fileURLWithPath: "/opt/homebrew/bin/python3")
guard let resources = Bundle.main.resourceURL else {
    FileHandle.standardError.write(Data("App resources are unavailable\n".utf8))
    exit(1)
}
let script = resources.appendingPathComponent("second_brain.py").path

let process = Process()
process.executableURL = python
process.arguments = ["-B", script, "snapshot"]

do {
    try process.run()
    process.waitUntilExit()
    exit(process.terminationStatus)
} catch {
    FileHandle.standardError.write(
        Data("Second Brain snapshot failed to start: \(error)\n".utf8)
    )
    exit(1)
}
