import Foundation

// Structures für API Responses
struct SearchResponse: Codable {
    let query: String
    let results: [ProductResult]
    let postalCode: String
    let totalResults: Int
    let searchTimeMs: Int
    
    enum CodingKeys: String, CodingKey {
        case query, results
        case postalCode = "postal_code"
        case totalResults = "total_results"
        case searchTimeMs = "search_time_ms"
    }
}

struct ProductResult: Codable, Identifiable {
    let id = UUID()
    let name: String
    let price: String
    let store: String
    let storeLogoUrl: String?
    let productUrl: String?
    let imageUrl: String?
    let availability: String
    let pricePerUnit: String?
    let unit: String?
    let offerValidUntil: String?
    
    private enum CodingKeys: String, CodingKey {
        case name, price, store, availability
        case storeLogoUrl = "store_logo_url"
        case productUrl = "product_url"
        case imageUrl = "image_url"
        case pricePerUnit = "price_per_unit"
        case unit
        case offerValidUntil = "offer_valid_until"
    }
}

struct Store: Codable {
    let storeId: String
    let name: String
    let logoUrl: String?
    let websiteUrl: String?
    let category: String
    
    enum CodingKeys: String, CodingKey {
        case storeId = "id"
        case name
        case logoUrl = "logo_url"
        case websiteUrl = "website_url"
        case category
    }
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
    
    init(name: String, query: String, postalCode: String, selectedStores: [String] = [], unit: String? = nil, maxPrice: Double? = nil) {
        self.id = UUID().uuidString
        self.name = name
        self.query = query
        self.postalCode = postalCode
        self.selectedStores = selectedStores
        self.unit = unit
        self.maxPrice = maxPrice
    }
} 