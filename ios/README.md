# Preisvergleich iOS App

Eine native iOS-App für den Preisvergleich deutscher Supermärkte, entwickelt mit SwiftUI.

## 🏗️ Projektstruktur

```
ios/
├── PreisvergleichApp.xcodeproj/     # Xcode-Projekt
├── PreisvergleichApp/
│   ├── PreisvergleichApp.swift      # Haupt-App-Datei
│   ├── Models/
│   │   └── Product.swift            # Datenmodelle
│   ├── Services/
│   │   └── APIService.swift         # API-Integration
│   ├── ViewModels/
│   │   └── SearchViewModel.swift    # ViewModel für Suchlogik
│   ├── Views/
│   │   └── ContentView.swift        # Haupt-UI
│   ├── Assets.xcassets/             # App-Assets
│   └── Preview Content/             # SwiftUI Previews
└── README.md                        # Diese Datei
```

## 🛠️ Technologie-Stack

| Technologie | Version | Zweck |
|-------------|---------|-------|
| SwiftUI | iOS 17+ | UI Framework |
| Combine | Built-in | Reactive Programming |
| URLSession | Built-in | HTTP-Requests |
| UserDefaults | Built-in | Lokale Datenspeicherung |

## ⚙️ Setup & Installation

### Voraussetzungen
- Xcode 15.0 oder höher
- iOS 17.0 oder höher
- macOS Monterey 12.0 oder höher

### Entwicklung starten

1. **Projekt öffnen**:
   ```bash
   cd ios
   open PreisvergleichApp.xcodeproj
   ```
   
   Oder öffnen Sie `PreisvergleichApp.xcodeproj` direkt in Xcode.

2. **Dependencies installieren**:
   - Alle Dependencies sind bereits integriert
   - Keine externen Package Manager erforderlich

3. **Backend starten**:
   Stellen Sie sicher, dass das Backend läuft:
   ```bash
   cd ../backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload
   ```

4. **App ausführen**:
   - Wählen Sie ein iOS-Simulator oder Device
   - Drücken Sie ⌘+R oder klicken Sie auf "Run"

## 🚨 Bekannte Probleme & Lösungen

### "overlapping sources" Fehler
**Problem gelöst**: Die ursprüngliche Swift Package Manager Struktur wurde durch ein traditionelles Xcode-Projekt ersetzt.

### Build-Fehler
- Stellen Sie sicher, dass das Deployment Target auf iOS 17.0 eingestellt ist
- Verwenden Sie Xcode 15.0 oder höher
- Alle SwiftUI und Combine Features sind für iOS 17+ verfügbar

## 🏗️ Architektur

### MVVM-Pattern
- **Model**: `Product.swift` - Datenstrukturen
- **ViewModel**: `SearchViewModel.swift` - Business Logic
- **View**: `ContentView.swift` - UI-Komponenten

### API-Integration
- `APIService.swift` verwaltet alle HTTP-Requests
- Combine Publisher für reaktive Programmierung
- Automatische JSON-Serialisierung mit Codable

### State Management
- `@StateObject` und `@Published` für UI-State
- UserDefaults für Postleitzahl-Persistierung
- Combine für asynchrone Datenströme

## 📱 Features

### ✅ Implementiert
- Produktsuche mit Postleitzahl
- Preisvergleich zwischen Supermärkten
- Sortierung nach Preis (niedrigster zuerst)
- Postleitzahl-Speicherung
- Moderne SwiftUI-Benutzeroberfläche
- Fehlerbehandlung und Loading-States

### 🚧 Roadmap
- [ ] Produktbilder von externen APIs
- [ ] Favoriten-Funktion
- [ ] Preishistorie-Tracking
- [ ] Push-Benachrichtigungen für Preisänderungen
- [ ] Barcode-Scanner
- [ ] Einkaufsliste-Feature
- [ ] Offline-Modus
- [ ] Widget-Support

## 🔧 API-Endpoints

Die App kommuniziert mit folgenden Backend-Endpoints:

- `POST /api/v1/search` - Produktsuche
- `GET /api/v1/stores` - Verfügbare Supermärkte
- `GET /api/v1/health` - Backend-Status

## 🎨 Design System

### Farben
- Primary: System Blue/Purple Gradient
- Success: System Green
- Error: System Red
- Background: System Background

### Typography
- Titel: Large Title (Bold)
- Headlines: Headline
- Body: Body
- Captions: Caption

### Components
- `ProductRowView`: Wiederverwendbare Produktzeile
- Gradient-Buttons für Call-to-Action
- Native iOS-Form-Elemente

## 🧪 Testing

### Unit Tests
```bash
# Tests ausführen
⌘+U in Xcode
```

### UI Tests
- SwiftUI Previews für schnelle UI-Tests
- Accessibility-Tests integriert

## 📝 Entwicklung

### Code-Stil
- Swift 5.9+ Features verwenden
- SwiftUI-Best-Practices befolgen
- Combine für Async-Operations
- MVVM-Architektur einhalten

### Debugging
- Xcode-Debugger verwenden
- Print-Statements für API-Calls
- SwiftUI-Preview für UI-Debugging

### Xcode-Projekt verwalten
- Verwenden Sie Xcode für alle Projektänderungen
- Neue Dateien über "Add Files to Project" hinzufügen
- Build Settings über Xcode Project Navigator konfigurieren

## 🤝 Beitragen

1. Branch erstellen: `git checkout -b feature/neue-funktion`
2. Änderungen committen: `git commit -m 'Add neue Funktion'`
3. Branch pushen: `git push origin feature/neue-funktion`
4. Pull Request erstellen

## 📄 Lizenz

Dieses Projekt ist Teil der Preisvergleich-App Suite. 