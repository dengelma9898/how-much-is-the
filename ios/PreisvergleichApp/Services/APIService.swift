import Foundation
import Combine

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

class APIService: ObservableObject {
    static let shared = APIService()
    
    private let baseURL = "http://localhost:8000/api/v1"
    private let session = URLSession.shared
    
    private init() {}
    
    // MARK: - Search Products
    func searchProducts(query: String, postalCode: String, selectedStores: [String]? = nil, unit: String? = nil, maxPrice: Double? = nil) -> AnyPublisher<SearchResponse, APIError> {
        guard let url = URL(string: "\(baseURL)/search") else {
            return Fail(error: APIError.invalidURL)
                .eraseToAnyPublisher()
        }
        
        let searchRequest = SearchRequest(query: query, postalCode: postalCode, selectedStores: selectedStores, unit: unit, maxPrice: maxPrice)
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            request.httpBody = try JSONEncoder().encode(searchRequest)
        } catch {
            return Fail(error: APIError.decodingError(error))
                .eraseToAnyPublisher()
        }
        
        return session.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: SearchResponse.self, decoder: JSONDecoder())
            .mapError { error in
                if error is DecodingError {
                    return APIError.decodingError(error)
                } else {
                    return APIError.networkError(error)
                }
            }
            .eraseToAnyPublisher()
    }
    
    // MARK: - Get Stores
    func getStores() -> AnyPublisher<[Store], APIError> {
        guard let url = URL(string: "\(baseURL)/stores") else {
            return Fail(error: APIError.invalidURL)
                .eraseToAnyPublisher()
        }
        
        return session.dataTaskPublisher(for: url)
            .map(\.data)
            .decode(type: StoresResponse.self, decoder: JSONDecoder())
            .map(\.stores)
            .mapError { error in
                if error is DecodingError {
                    return APIError.decodingError(error)
                } else {
                    return APIError.networkError(error)
                }
            }
            .eraseToAnyPublisher()
    }
    
    // MARK: - Health Check
    func healthCheck() -> AnyPublisher<Bool, APIError> {
        guard let url = URL(string: "\(baseURL)/health") else {
            return Fail(error: APIError.invalidURL)
                .eraseToAnyPublisher()
        }
        
        return session.dataTaskPublisher(for: url)
            .map { _ in true }
            .mapError { APIError.networkError($0) }
            .eraseToAnyPublisher()
    }
} 