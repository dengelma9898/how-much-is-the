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
    @Published var savedSearches: [SavedSearch] = []
    @Published var filtersEnabled = true
    @Published var showSaveButton = false
    
    private let apiService = APIService.shared
    private var cancellables = Set<AnyCancellable>()
    private let savedSearchesKey = "saved_searches"
    
    init() {
        loadPostalCode()
        loadStores()
        loadSavedSearches()
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
        showSaveButton = false
        
        apiService.searchProducts(
            query: searchQuery,
            postalCode: postalCode,
            selectedStores: filtersEnabled && !selectedStoreIds.isEmpty ? selectedStoreIds : nil,
            unit: filtersEnabled ? selectedUnit : nil,
            maxPrice: filtersEnabled ? maxPrice : nil
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
                self?.showSaveButton = !response.results.isEmpty
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
    
    // MARK: - Saved Searches
    private func loadSavedSearches() {
        if let data = UserDefaults.standard.data(forKey: savedSearchesKey),
           let searches = try? JSONDecoder().decode([SavedSearch].self, from: data) {
            savedSearches = searches
        }
    }
    
    private func saveSavedSearches() {
        if let data = try? JSONEncoder().encode(savedSearches) {
            UserDefaults.standard.set(data, forKey: savedSearchesKey)
        }
    }
    
    func saveCurrentSearch(name: String) {
        let newSearch = SavedSearch(
            name: name,
            query: searchQuery,
            postalCode: postalCode,
            selectedStores: selectedStoreIds,
            unit: selectedUnit,
            maxPrice: maxPrice
        )
        
        savedSearches.append(newSearch)
        saveSavedSearches()
        showSaveButton = false
    }
    
    func loadSavedSearch(_ savedSearch: SavedSearch) {
        searchQuery = savedSearch.query
        postalCode = savedSearch.postalCode
        
        if filtersEnabled {
            selectedStoreIds = savedSearch.selectedStores
            selectedUnit = savedSearch.unit
            maxPrice = savedSearch.maxPrice
        } else {
            selectedStoreIds = []
            selectedUnit = nil
            maxPrice = nil
        }
        
        // Automatisch suchen nach dem Laden
        searchProducts()
    }
    
    func deleteSavedSearch(_ search: SavedSearch) {
        savedSearches.removeAll { $0.id == search.id }
        saveSavedSearches()
    }
    
    func toggleFilters() {
        filtersEnabled.toggle()
    }
    
    func hideSaveButton() {
        showSaveButton = false
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