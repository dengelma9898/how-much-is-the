import Foundation
import Combine

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