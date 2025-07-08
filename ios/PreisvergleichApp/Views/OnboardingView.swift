import SwiftUI

struct OnboardingPage {
    let title: String
    let description: String
    let systemImage: String
    let backgroundColor: Color
}

struct OnboardingView: View {
    @Binding var isCompleted: Bool
    @State private var currentPage = 0
    
    private let pages = [
        OnboardingPage(
            title: "Preise vergleichen",
            description: "Finden Sie die besten Preise für Ihre Lieblings-Produkte in deutschen Supermärkten.",
            systemImage: "magnifyingglass",
            backgroundColor: .blue
        ),
        OnboardingPage(
            title: "Geld sparen",
            description: "Sparen Sie bei jedem Einkauf Geld durch intelligente Preisvergleiche.",
            systemImage: "banknote",
            backgroundColor: .green
        ),
        OnboardingPage(
            title: "Einfach & schnell",
            description: "Suchen Sie einfach nach Produkten und finden Sie sofort die günstigsten Angebote in Ihrer Nähe.",
            systemImage: "bolt.fill",
            backgroundColor: .orange
        )
    ]
    
    var body: some View {
        VStack {
            HStack {
                Spacer()
                Button("Überspringen") {
                    isCompleted = true
                }
                .foregroundColor(.primary)
                .padding()
            }
            
            TabView(selection: $currentPage) {
                ForEach(0..<pages.count, id: \.self) { index in
                    OnboardingPageView(page: pages[index])
                        .tag(index)
                }
            }
            .tabViewStyle(PageTabViewStyle(indexDisplayMode: .never))
            
            // Custom Page Indicator
            HStack(spacing: 8) {
                ForEach(0..<pages.count, id: \.self) { index in
                    Circle()
                        .fill(currentPage == index ? Color.primary : Color.gray.opacity(0.4))
                        .frame(width: currentPage == index ? 12 : 8, height: currentPage == index ? 12 : 8)
                        .animation(.easeInOut(duration: 0.3), value: currentPage)
                }
            }
            .padding(.vertical)
            
            // Navigation Buttons
            HStack {
                if currentPage > 0 {
                    Button("Zurück") {
                        withAnimation(.easeInOut(duration: 0.3)) {
                            currentPage -= 1
                        }
                    }
                    .foregroundColor(.primary)
                } else {
                    Spacer()
                }
                
                Spacer()
                
                Button(action: {
                    if currentPage < pages.count - 1 {
                        withAnimation(.easeInOut(duration: 0.3)) {
                            currentPage += 1
                        }
                    } else {
                        isCompleted = true
                    }
                }) {
                    Text(currentPage < pages.count - 1 ? "Weiter" : "Los geht's!")
                        .font(.headline)
                        .foregroundColor(.white)
                        .padding(.horizontal, 30)
                        .padding(.vertical, 12)
                        .background(
                            LinearGradient(
                                gradient: Gradient(colors: [.blue, .purple]),
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .cornerRadius(25)
                }
            }
            .padding(.horizontal)
            .padding(.bottom, 30)
        }
        .background(Color(.systemBackground))
    }
}

struct OnboardingPageView: View {
    let page: OnboardingPage
    
    var body: some View {
        VStack(spacing: 40) {
            Spacer()
            
            // Icon
            ZStack {
                Circle()
                    .fill(page.backgroundColor.opacity(0.2))
                    .frame(width: 120, height: 120)
                
                Image(systemName: page.systemImage)
                    .font(.system(size: 50))
                    .foregroundColor(page.backgroundColor)
            }
            
            VStack(spacing: 16) {
                Text(page.title)
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.primary)
                
                Text(page.description)
                    .font(.body)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 32)
                    .lineLimit(nil)
            }
            
            Spacer()
        }
        .padding()
    }
}

#Preview {
    OnboardingView(isCompleted: .constant(false))
} 