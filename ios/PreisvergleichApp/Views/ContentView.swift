import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = SearchViewModel()
    @State private var showFilterSheet = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header
                VStack(spacing: 8) {
                    Text("Preisvergleich")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.primary)
                    
                    Text("Finden Sie die besten Preise in deutschen Supermärkten")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(.top)
                
                // Search Form
                VStack(spacing: 16) {
                    // Search Query Input + Filter Icon
                    HStack(alignment: .bottom) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Was suchen Sie?")
                                .font(.headline)
                                .foregroundColor(.primary)
                            
                            TextField("z.B. Milch, Eier, Oatly, Haribo...", text: $viewModel.searchQuery)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .submitLabel(.search)
                                .onSubmit {
                                    viewModel.searchProducts()
                                }
                        }
                        Spacer(minLength: 8)
                        ZStack(alignment: .topTrailing) {
                            Button(action: {
                                withAnimation(.spring(response: 0.3, dampingFraction: 0.6, blendDuration: 0.5)) {
                                    showFilterSheet = true
                                }
                            }) {
                                Image(systemName: "line.3.horizontal.decrease.circle")
                                    .font(.title2)
                                    .foregroundColor(viewModel.selectedStoreIds.isEmpty && viewModel.selectedUnit == nil && viewModel.maxPrice == nil ? .gray : .blue)
                                    .padding(8)
                                    .background(
                                        Group {
                                            if !(viewModel.selectedStoreIds.isEmpty && viewModel.selectedUnit == nil && viewModel.maxPrice == nil) {
                                                Circle().fill(Color.blue.opacity(0.15))
                                            } else {
                                                Color.clear
                                            }
                                        }
                                    )
                                    .scaleEffect(showFilterSheet ? 1.15 : 1.0)
                                    .animation(.spring(response: 0.3, dampingFraction: 0.7), value: showFilterSheet)
                            }
                            .accessibilityLabel("Filter anzeigen")
                            // Badge für aktive Filter
                            if !(viewModel.selectedStoreIds.isEmpty && viewModel.selectedUnit == nil && viewModel.maxPrice == nil) {
                                Circle()
                                    .fill(Color.red)
                                    .frame(width: 10, height: 10)
                                    .offset(x: 8, y: -8)
                                    .transition(.scale)
                            }
                        }
                    }
                    
                    // Postal Code Input
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Postleitzahl")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        TextField("z.B. 10115", text: $viewModel.postalCode)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.numberPad)
                    }
                    
                    // Search Button
                    Button(action: {
                        viewModel.searchProducts()
                    }) {
                        HStack {
                            if viewModel.isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "magnifyingglass")
                            }
                            Text(viewModel.isLoading ? "Suche läuft..." : "Preise vergleichen")
                        }
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(
                            LinearGradient(
                                gradient: Gradient(colors: [.blue, .purple]),
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .cornerRadius(12)
                    }
                    .disabled(viewModel.isLoading || viewModel.searchQuery.isEmpty || viewModel.postalCode.isEmpty)
                }
                .padding(.horizontal)
                
                // Error Message
                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .font(.caption)
                        .padding(.horizontal)
                }
                
                // Results List
                if viewModel.hasResults {
                    List(viewModel.sortedProducts) { product in
                        ProductRowView(product: product)
                            .listRowSeparator(.hidden)
                            .padding(.vertical, 4)
                    }
                    .listStyle(PlainListStyle())
                } else if !viewModel.isLoading && viewModel.searchQuery.isEmpty {
                    // Empty State
                    VStack(spacing: 12) {
                        Image(systemName: "cart.badge.plus")
                            .font(.system(size: 60))
                            .foregroundColor(.gray)
                        
                        Text("Starten Sie Ihre Preissuche")
                            .font(.title2)
                            .fontWeight(.medium)
                            .foregroundColor(.primary)
                        
                        Text("Geben Sie ein Produkt und Ihre Postleitzahl ein, um die besten Preise zu finden.")
                            .font(.body)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                }
                
                Spacer()
            }
            .sheet(isPresented: $showFilterSheet) {
                NavigationView {
                    VStack(spacing: 20) {
                        // Store Multi-Select
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Supermärkte filtern")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 8) {
                                    ForEach(viewModel.stores, id: \ .storeId) { store in
                                        let isSelected = viewModel.selectedStoreIds.contains(store.storeId)
                                        Button(action: {
                                            if isSelected {
                                                viewModel.selectedStoreIds.removeAll { $0 == store.storeId }
                                            } else {
                                                viewModel.selectedStoreIds.append(store.storeId)
                                            }
                                        }) {
                                            HStack(spacing: 4) {
                                                if let logoUrl = store.logoUrl, let url = URL(string: logoUrl) {
                                                    AsyncImage(url: url) { image in
                                                        image.resizable().scaledToFit()
                                                    } placeholder: {
                                                        Color.gray.opacity(0.2)
                                                    }
                                                    .frame(width: 20, height: 20)
                                                    .clipShape(Circle())
                                                }
                                                Text(store.name)
                                                    .font(.caption)
                                                    .foregroundColor(isSelected ? .white : .primary)
                                            }
                                            .padding(.horizontal, 10)
                                            .padding(.vertical, 6)
                                            .background(isSelected ? Color.blue : Color(.systemGray5))
                                            .cornerRadius(16)
                                        }
                                    }
                                }
                            }
                        }
                        // Einheit
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Einheit filtern (optional)")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            TextField("z.B. 1L, 500g", text: Binding(
                                get: { viewModel.selectedUnit ?? "" },
                                set: { viewModel.selectedUnit = $0.isEmpty ? nil : $0 }
                            ))
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                        }
                        // Maximalpreis
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Maximalpreis (optional)")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            HStack {
                                Slider(value: Binding(
                                    get: { viewModel.maxPrice ?? 10.0 },
                                    set: { viewModel.maxPrice = $0 }
                                ), in: 0...10, step: 0.1)
                                TextField("", text: Binding(
                                    get: { viewModel.maxPrice != nil ? String(format: "%.2f", viewModel.maxPrice!) : "" },
                                    set: { viewModel.maxPrice = Double($0.replacingOccurrences(of: ",", with: ".")) }
                                ))
                                .frame(width: 60)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .keyboardType(.decimalPad)
                                Text("€")
                                    .foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                    }
                    .padding()
                    .navigationTitle("Filter")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Schließen") { showFilterSheet = false }
                        }
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Fertig") { showFilterSheet = false }
                        }
                    }
                }
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
            }
        }
    }
}

struct ProductRowView: View {
    let product: ProductResult
    
    var body: some View {
        HStack(spacing: 12) {
            // Product Image Placeholder
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.gray.opacity(0.3))
                .frame(width: 60, height: 60)
                .overlay(
                    Image(systemName: "photo")
                        .foregroundColor(.gray)
                )
            
            // Product Info
            VStack(alignment: .leading, spacing: 4) {
                Text(product.name)
                    .font(.headline)
                    .foregroundColor(.primary)
                    .lineLimit(2)
                
                Text(product.store)
                    .font(.subheadline)
                    .foregroundColor(.blue)
                
                Text(product.availability)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            // Price
            VStack(alignment: .trailing) {
                Text(product.price)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.green)
                
                Text("€")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .gray.opacity(0.2), radius: 4, x: 0, y: 2)
    }
}

#Preview {
    ContentView()
} 