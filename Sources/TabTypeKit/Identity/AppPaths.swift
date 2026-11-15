import Foundation

/// Locations owned by Keytypist. Construction and getters only compute URLs:
/// they never inspect, create, migrate, or remove files or directories.
public struct AppPaths: Sendable {
    public let homeDirectory: URL

    public init(homeDirectory: URL) {
        self.homeDirectory = homeDirectory
    }

    /// Controlled test processes may supply an absolute `KEYTYPIST_TEST_HOME`.
    /// Relative paths, empty values, and tilde paths are ignored. This override
    /// does not change `HOME` or create the supplied directory.
    public static var current: AppPaths {
        if let path = ProcessInfo.processInfo.environment["KEYTYPIST_TEST_HOME"], path.hasPrefix("/") {
            return AppPaths(homeDirectory: URL(fileURLWithPath: path, isDirectory: true))
        }
        return AppPaths(homeDirectory: FileManager.default.homeDirectoryForCurrentUser)
    }

    public var supportDirectory: URL {
        homeDirectory.appendingPathComponent("Library/Application Support/Keytypist", isDirectory: true)
    }

    public var modelsDirectory: URL {
        supportDirectory.appendingPathComponent("Models", isDirectory: true)
    }

    public var cacheDirectory: URL {
        homeDirectory.appendingPathComponent("Library/Caches/Keytypist", isDirectory: true)
    }

    public var logsDirectory: URL {
        homeDirectory.appendingPathComponent("Library/Logs/Keytypist", isDirectory: true)
    }

    public var fitCapturesDirectory: URL {
        logsDirectory.appendingPathComponent("fit", isDirectory: true)
    }

    public var syncDirectory: URL {
        homeDirectory.appendingPathComponent(
            "Library/Mobile Documents/com~apple~CloudDocs/\(ProductIdentity.syncFolderName)", isDirectory: true)
    }
}
