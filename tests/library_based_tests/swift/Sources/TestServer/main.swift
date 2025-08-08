
import Foundation
import SwiftJanus

@main
struct ServerApp {
    static func main() async {
        let socketPath = CommandLine.arguments[1]
        
        // Remove existing socket
        try? FileManager.default.removeItem(atPath: socketPath)
        
        do {
            let server = JanusServer()
            try await server.startListening(socketPath)
            
            print("SERVER_READY")
            fflush(stdout)
            
            // Keep server running by waiting for termination signal
            // The server now runs in background task, so we just wait
            while true {
                try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
            }
        } catch {
            print("Failed to start server: \(error)")
            exit(1)
        }
    }
}
