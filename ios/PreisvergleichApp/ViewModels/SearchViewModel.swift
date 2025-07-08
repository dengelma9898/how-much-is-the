import Foundation
import Combine
import SwiftUI

class SearchViewModel: ObservableObject {
    @Published var searchQuery = ""
    @Published var postalCode = ""
    @Published var products: [ProductResult] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var stores: [Store] = []
    @Published var selectedStoreIds: [String] = []
    @Published var selectedUnit: String? = nil
    @Published var maxPrice: Double? = nil
    
    private let apiService = APIService.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        loadPostalCode()
        loadStores()
    }
    
    // MARK: - Search Products
    func searchProducts() {
        guard !searchQuery.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              !postalCode.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Bitte geben Sie einen Suchbegriff und eine Postleitzahl ein."
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        apiService.searchProducts(
            query: searchQuery,
            postalCode: postalCode,
            selectedStores: selectedStoreIds.isEmpty ? nil : selectedStoreIds,
            unit: selectedUnit,
            maxPrice: maxPrice
        )
        .receive(on: DispatchQueue.main)
        .sink(
            receiveCompletion: { [weak self] completion in
                self?.isLoading = false
                if case .failure(let error) = completion {
                    self?.errorMessage = error.localizedDescription
                }
            },
            receiveValue: { [weak self] response in
                self?.products = response.results
                self?.savePostalCode()
            }
        )
        .store(in: &cancellables)
    }
    
    // MARK: - Load Stores
    private func loadStores() {
        apiService.getStores()
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { completion in
                    if case .failure(let error) = completion {
                        print("Fehler beim Laden der Stores: \(error)")
                    }
                },
                receiveValue: { [weak self] stores in
                    self?.stores = stores
                }
            )
            .store(in: &cancellables)
    }
    
    // MARK: - Postal Code Persistence
    private func loadPostalCode() {
        postalCode = UserDefaults.standard.string(forKey: "saved_postal_code") ?? ""
    }
    
    private func savePostalCode() {
        UserDefaults.standard.set(postalCode, forKey: "saved_postal_code")
    }
    
    // MARK: - Helpers
    func clearResults() {
        products.removeAll()
        errorMessage = nil
    }
    
    var hasResults: Bool {
        !products.isEmpty
    }
    
    var sortedProducts: [ProductResult] {
        products.sorted { product1, product2 in
            let price1 = Double(product1.price.replacingOccurrences(of: "€", with: "").replacingOccurrences(of: ",", with: ".")) ?? 0
            let price2 = Double(product2.price.replacingOccurrences(of: "€", with: "").replacingOccurrences(of: ",", with: ".")) ?? 0
            return price1 < price2
        }
    }
} 