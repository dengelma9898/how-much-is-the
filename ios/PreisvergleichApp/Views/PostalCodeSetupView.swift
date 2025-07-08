import SwiftUI

struct PostalCodeSetupView: View {
    @State private var postalCode = ""
    @State private var isError = false
    @FocusState private var isTextFieldFocused: Bool
    
    let onComplete: (String) -> Void
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            // Icon
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
                    .lineLimit(nil)
            }
            
            VStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 8) {
                    TextField("z.B. 10115", text: $postalCode)
                        .keyboardType(.numberPad)
                        .focused($isTextFieldFocused)
                        .onChange(of: postalCode) { _, newValue in
                            // Only allow digits and limit to 5 characters
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
                        .background(
                            LinearGradient(
                                gradient: Gradient(colors: [.blue, .purple]),
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
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
    PostalCodeSetupView { postalCode in
        print("Postal code: \(postalCode)")
    }
} 