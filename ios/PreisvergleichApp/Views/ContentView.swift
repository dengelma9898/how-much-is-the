import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = SearchViewModel()
    @State private var isOnboardingCompleted = UserDefaults.standard.bool(forKey: "isOnboardingCompleted")
    @State private var savedPostalCode = UserDefaults.standard.string(forKey: "postalCode") ?? ""
    @State private var showFilterSheet = false
    @State private var showOnboarding = false
    @State private var showPostalCodeSetup = false
    
    var body: some View {
        Group {
            if showOnboarding {
                SimpleOnboardingView { 
                    showOnboarding = false
                }
            } else if showPostalCodeSetup {
                SimplePostalCodeSetupView { postalCode in
                    if !postalCode.isEmpty {
                        UserDefaults.standard.set(postalCode, forKey: "postalCode")
                        savedPostalCode = postalCode
                        viewModel.postalCode = postalCode
                    }
                    showPostalCodeSetup = false
                }
            } else {
                mainContentView
            }
        }
        .onAppear {
            setupInitialState()
        }
        .onChange(of: showOnboarding) { _, newValue in
            if !newValue {
                UserDefaults.standard.set(true, forKey: "isOnboardingCompleted")
                isOnboardingCompleted = true
                checkPostalCodeSetup()
            }
        }
    }
    
    private var mainContentView: some View {
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
                    .disabled(viewModel.isLoading || viewModel.searchQuery.isEmpty)
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
                        
                        Text("Geben Sie ein Produkt ein, um die besten Preise zu finden.")
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
                        
                        // Postleitzahl
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Postleitzahl")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            
                            HStack {
                                TextField("z.B. 10115", text: $viewModel.postalCode)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .keyboardType(.numberPad)
                                
                                Button("Ändern") {
                                    UserDefaults.standard.set(viewModel.postalCode, forKey: "postalCode")
                                    savedPostalCode = viewModel.postalCode
                                }
                                .buttonStyle(.bordered)
                                .disabled(viewModel.postalCode.count != 5)
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
    
    // MARK: - Setup Methods
    private func setupInitialState() {
        if !isOnboardingCompleted {
            showOnboarding = true
        } else if savedPostalCode.isEmpty {
            showPostalCodeSetup = true
        } else {
            // Initialize with saved postal code
            viewModel.postalCode = savedPostalCode
        }
    }
    
    private func checkPostalCodeSetup() {
        if savedPostalCode.isEmpty {
            showPostalCodeSetup = true
        } else {
            viewModel.postalCode = savedPostalCode
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

// MARK: - Simple Onboarding Views

struct SimpleOnboardingView: View {
    let onCompleted: () -> Void
    @State private var currentPage = 0
    
    private let pages = [
        ("Preise vergleichen", "Finden Sie die besten Preise für Ihre Lieblings-Produkte in deutschen Supermärkten.", "magnifyingglass"),
        ("Geld sparen", "Sparen Sie bei jedem Einkauf Geld durch intelligente Preisvergleiche.", "banknote"),
        ("Einfach & schnell", "Suchen Sie einfach nach Produkten und finden Sie sofort die günstigsten Angebote in Ihrer Nähe.", "bolt.fill")
    ]
    
    var body: some View {
        VStack {
            HStack {
                Spacer()
                Button("Überspringen") {
                    onCompleted()
                }
                .foregroundColor(.primary)
                .padding()
            }
            
            TabView(selection: $currentPage) {
                ForEach(0..<pages.count, id: \.self) { index in
                    VStack(spacing: 40) {
                        Spacer()
                        
                        ZStack {
                            Circle()
                                .fill(Color.blue.opacity(0.2))
                                .frame(width: 120, height: 120)
                            
                            Image(systemName: pages[index].2)
                                .font(.system(size: 50))
                                .foregroundColor(.blue)
                        }
                        
                        VStack(spacing: 16) {
                            Text(pages[index].0)
                                .font(.largeTitle)
                                .fontWeight(.bold)
                                .multilineTextAlignment(.center)
                                .foregroundColor(.primary)
                            
                            Text(pages[index].1)
                                .font(.body)
                                .multilineTextAlignment(.center)
                                .foregroundColor(.secondary)
                                .padding(.horizontal, 32)
                        }
                        
                        Spacer()
                    }
                    .tag(index)
                }
            }
            .tabViewStyle(PageTabViewStyle(indexDisplayMode: .never))
            
            HStack(spacing: 8) {
                ForEach(0..<pages.count, id: \.self) { index in
                    Circle()
                        .fill(currentPage == index ? Color.primary : Color.gray.opacity(0.4))
                        .frame(width: currentPage == index ? 12 : 8, height: currentPage == index ? 12 : 8)
                        .animation(.easeInOut(duration: 0.3), value: currentPage)
                }
            }
            .padding(.vertical)
            
            HStack {
                if currentPage > 0 {
                    Button("Zurück") {
                        withAnimation { currentPage -= 1 }
                    }
                    .foregroundColor(.primary)
                } else {
                    Spacer()
                }
                
                Spacer()
                
                Button(action: {
                    if currentPage < pages.count - 1 {
                        withAnimation { currentPage += 1 }
                    } else {
                        onCompleted()
                    }
                }) {
                    Text(currentPage < pages.count - 1 ? "Weiter" : "Los geht's!")
                        .font(.headline)
                        .foregroundColor(.white)
                        .padding(.horizontal, 30)
                        .padding(.vertical, 12)
                        .background(LinearGradient(gradient: Gradient(colors: [.blue, .purple]), startPoint: .leading, endPoint: .trailing))
                        .cornerRadius(25)
                }
            }
            .padding(.horizontal)
            .padding(.bottom, 30)
        }
        .background(Color(.systemBackground))
    }
}

struct SimplePostalCodeSetupView: View {
    @State private var postalCode = ""
    @State private var isError = false
    @FocusState private var isTextFieldFocused: Bool
    
    let onComplete: (String) -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            ZStack {
                Circle()
                    .fill(Color.blue.opacity(0.2))
                    .frame(width: 100, height: 100)
                
                Image(systemName: "location.circle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.blue)
            }
            
            VStack(spacing: 16) {
                Text("Ihre Postleitzahl")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.primary)
                
                Text("Geben Sie Ihre Postleitzahl ein, um lokale Angebote und Supermärkte in Ihrer Nähe zu finden.")
                    .font(.body)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 32)
            }
            
            VStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 8) {
                    TextField("z.B. 10115", text: $postalCode)
                        .keyboardType(.numberPad)
                        .focused($isTextFieldFocused)
                        .onChange(of: postalCode) { _, newValue in
                            let filtered = newValue.filter { $0.isNumber }
                            if filtered.count <= 5 {
                                postalCode = filtered
                                isError = false
                            } else {
                                postalCode = String(filtered.prefix(5))
                            }
                        }
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(isError ? Color.red : Color.clear, lineWidth: 1)
                        )
                    
                    if isError {
                        Text("Bitte geben Sie eine gültige 5-stellige Postleitzahl ein")
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                }
                .padding(.horizontal, 24)
                
                Button(action: {
                    if postalCode.count == 5 {
                        onComplete(postalCode)
                    } else {
                        isError = true
                    }
                }) {
                    Text("Weiter")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(LinearGradient(gradient: Gradient(colors: [.blue, .purple]), startPoint: .leading, endPoint: .trailing))
                        .cornerRadius(12)
                        .opacity(postalCode.isEmpty ? 0.6 : 1.0)
                }
                .disabled(postalCode.isEmpty)
                .padding(.horizontal, 24)
                
                Button("Später eingeben") {
                    onComplete("")
                }
                .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .background(Color(.systemBackground))
        .onAppear {
            isTextFieldFocused = true
        }
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("Fertig") {
                    isTextFieldFocused = false
                }
            }
        }
    }
}



#Preview {
    ContentView()
} 