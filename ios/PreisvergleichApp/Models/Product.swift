import Foundation

// Structures für API Responses
struct SearchResponse: Codable {
    let query: String
    let results: [ProductResult]
}

struct ProductResult: Codable, Identifiable {
    let id = UUID()
    let name: String
    let price: String
    let store: String
    let availability: String
    
    private enum CodingKeys: String, CodingKey {
        case name, price, store, availability
    }
}

struct Store: Codable {
    let storeId: String
    let name: String
    let logoUrl: String?
}

// Saved Search Model
struct SavedSearch: Codable, Identifiable {
    let id: String
    let name: String
    let query: String
    let postalCode: String
    let selectedStores: [String]
    let unit: String?
    let maxPrice: Double?
    
    init(name: String, query: String, postalCode: String, selectedStores: [String], unit: String?, maxPrice: Double?) {
        self.id = UUID().uuidString
        self.name = name
        self.query = query
        self.postalCode = postalCode
        self.selectedStores = selectedStores
        self.unit = unit
        self.maxPrice = maxPrice
    }
} 