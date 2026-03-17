import SwiftUI
import CoreData

@main
struct meta_ai_appApp: App {
    let persistenceController = PersistenceController.shared

    // Prevent macOS from throttling/suspending the app when minimized
    private let activityToken = ProcessInfo.processInfo.beginActivity(
        options: [.userInitiated, .idleSystemSleepDisabled],
        reason: "Downloading videos in background"
    )

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.managedObjectContext, persistenceController.container.viewContext)
        }
    }
}
