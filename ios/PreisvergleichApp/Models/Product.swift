import Foundation

// MARK: - API Request Models
struct SearchRequest: Codable {
    let query: String
    let postalCode: String
    let selectedStores: [String]?
    let unit: String?
    let maxPrice: Double?
    
    enum CodingKeys: String, CodingKey {
        case query
        case postalCode = "postal_code"
        case selectedStores = "selected_stores"
        case unit
        case maxPrice = "max_price"
    }
}

// MARK: - API Response Models
struct SearchResponse: Codable {
    let results: [ProductResult]
    let query: String
    let postalCode: String
    let totalResults: Int
    let searchTimeMs: Int
    
    enum CodingKeys: String, CodingKey {
        case results
        case query
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
    let availability: String
    let imageUrl: String?
    let productUrl: String?
    let storeLogoUrl: String?
    let unit: String?
    let pricePerUnit: String?
    
    enum CodingKeys: String, CodingKey {
        case name, price, store, availability, unit
        case imageUrl = "image_url"
        case productUrl = "product_url"
        case storeLogoUrl = "store_logo_url"
        case pricePerUnit = "price_per_unit"
    }
}

struct Store: Codable, Identifiable {
    let storeId: String
    let name: String
    let logoUrl: String?
    let websiteUrl: String?
    let category: String
    
    var id: String { storeId }
    
    enum CodingKeys: String, CodingKey {
        case storeId = "id"
        case name
        case logoUrl = "logo_url"
        case websiteUrl = "website_url"
        case category
    }
}

struct StoresResponse: Codable {
    let stores: [Store]
}

// MARK: - API Error
enum APIError: Error, LocalizedError {
    case invalidURL
    case noData
    case decodingError(Error)
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Ungültige URL"
        case .noData:
            return "Keine Daten erhalten"
        case .decodingError(let error):
            return "Dekodierungsfehler: \(error.localizedDescription)"
        case .networkError(let error):
            return "Netzwerkfehler: \(error.localizedDescription)"
        }
    }
} 