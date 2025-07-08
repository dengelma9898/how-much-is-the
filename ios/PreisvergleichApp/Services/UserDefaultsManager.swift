import Foundation
import Combine

class UserDefaultsManager: ObservableObject {
    static let shared = UserDefaultsManager()
    
    // Keys for UserDefaults
    private enum Keys {
        static let isOnboardingCompleted = "isOnboardingCompleted"
        static let postalCode = "postalCode"
    }
    
    // Published properties
    @Published var isOnboardingCompleted: Bool {
        didSet {
            UserDefaults.standard.set(isOnboardingCompleted, forKey: Keys.isOnboardingCompleted)
        }
    }
    
    @Published var postalCode: String {
        didSet {
            UserDefaults.standard.set(postalCode, forKey: Keys.postalCode)
        }
    }
    
    private init() {
        self.isOnboardingCompleted = UserDefaults.standard.bool(forKey: Keys.isOnboardingCompleted)
        self.postalCode = UserDefaults.standard.string(forKey: Keys.postalCode) ?? ""
    }
    
    // Methods
    func completeOnboarding() {
        isOnboardingCompleted = true
    }
    
    func savePostalCode(_ code: String) {
        postalCode = code
    }
    
    func clearAll() {
        UserDefaults.standard.removeObject(forKey: Keys.isOnboardingCompleted)
        UserDefaults.standard.removeObject(forKey: Keys.postalCode)
        isOnboardingCompleted = false
        postalCode = ""
    }
} 