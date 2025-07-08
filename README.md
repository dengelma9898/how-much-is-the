# Preisvergleich App 🛒

Eine moderne Preisvergleichs-App für deutsche Supermärkte mit Android, iOS und Python Backend.

## 🚀 Schnellstart

### 1. Repository klonen
```bash
git clone <repository-url>
cd how-much-is-the
```

### 2. Backend starten
```bash
cd backend
./start.sh
```

Das Backend läuft dann auf: http://localhost:8000
- API Dokumentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

### 3. Mobile Apps

#### Android
```bash
cd android
./start.sh
```
Dann in Android Studio öffnen oder mit Gradle CLI verwenden.

#### iOS
```bash
cd ios
./start.sh
```
Dann in Xcode öffnen: `open PreisvergleichApp.xcodeproj`

## 📱 Features

- **Produktsuche**: Suche nach Produkten in verschiedenen Supermärkten
- **Regionale Preise**: Preise basierend auf Postleitzahl
- **Preisvergleich**: Sortierung nach niedrigstem Preis
- **Mehrere Supermärkte**: REWE, EDEKA, Lidl, ALDI, Kaufland, dm, Rossmann
- **Cross-Platform**: Native Android & iOS Apps mit gemeinsamem Backend

## 🛠 Tech Stack

| Komponente | Technologie | Version |
|------------|-------------|---------|
| **Backend** | Python FastAPI | 0.115.0 |
| **Database** | Mock Data Service | - |
| **Web Scraping** | Firecrawl | 0.0.20 |
| **Android** | Kotlin + Jetpack Compose | 2.1.0 |
| **iOS** | Swift + SwiftUI | iOS 17+ |
| **API Client** | Retrofit (Android), URLSession (iOS) | - |

## 📚 API Endpunkte

### Backend API (Port 8000)

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health Check |
| `POST` | `/api/v1/search` | Produktsuche |
| `GET` | `/api/v1/stores` | Verfügbare Supermärkte |

### Beispiel API Request
```bash
# Produktsuche
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Milch",
    "postal_code": "10115"
  }'

# Health Check
curl http://localhost:8000/api/v1/health
```

## 🔧 Setup Details

### Systemvoraussetzungen

#### Backend
- Python 3.9+
- pip3

#### Android
- Android Studio Arctic Fox+
- Kotlin 2.1.0+
- Android SDK 34+

#### iOS
- Xcode 15+
- iOS 17.0+
- macOS mit Apple Silicon oder Intel

### Manuelle Installation

#### Backend Setup
```bash
cd backend

# Abhängigkeiten installieren
pip3 install -r requirements.txt

# Server starten
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Android Setup
```bash
cd android

# Gradle build
./gradlew build

# APK erstellen
./gradlew assembleDebug

# Auf Gerät installieren
./gradlew installDebug
```

#### iOS Setup
```bash
cd ios

# Xcode build
xcodebuild -project PreisvergleichApp.xcodeproj -scheme PreisvergleichApp build

# Oder in Xcode öffnen
open PreisvergleichApp.xcodeproj
```

## 📁 Projektstruktur

```
how-much-is-the/
├── backend/                 # Python FastAPI Backend
│   ├── app/
│   │   ├── core/           # Konfiguration
│   │   ├── models/         # Datenmodelle
│   │   ├── routers/        # API Endpoints
│   │   ├── services/       # Business Logic
│   │   └── main.py         # FastAPI App
│   ├── requirements.txt    # Python Dependencies
│   └── start.sh           # Start Script
├── android/                # Android Kotlin App
│   ├── app/
│   │   └── src/main/java/com/preisvergleich/android/
│   │       ├── data/       # Data Layer
│   │       ├── MainActivity.kt
│   │       └── PreisvergleichApplication.kt
│   ├── build.gradle.kts   # Build Configuration
│   └── start.sh          # Start Script
├── ios/                   # iOS Swift App
│   ├── PreisvergleichApp/
│   │   ├── Models/        # Data Models
│   │   ├── Views/         # SwiftUI Views
│   │   ├── ViewModels/    # ViewModels
│   │   ├── Services/      # API Services
│   │   └── Assets.xcassets
│   ├── PreisvergleichApp.xcodeproj
│   └── start.sh          # Start Script
└── README.md             # Diese Datei
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python3 -m pytest
```

### Android Tests
```bash
cd android
./gradlew test
```

### iOS Tests
```bash
cd ios
xcodebuild -project PreisvergleichApp.xcodeproj -scheme PreisvergleichApp test
```

## 🔍 Troubleshooting

### PATH-Probleme (macOS)
Falls pip3 nicht gefunden wird:
```bash
export PATH="/Users/$USER/Library/Python/3.9/bin:$PATH"
echo 'export PATH="/Users/$USER/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
```

### Backend startet nicht
1. Python Version prüfen: `python3 --version`
2. Dependencies installieren: `pip3 install -r requirements.txt`
3. Port prüfen: `lsof -i :8000`

### Android Build Fehler
1. Android Studio installiert?
2. SDK Version 34+ installiert?
3. `./gradlew clean build`

### iOS Build Fehler
1. Xcode 15+ installiert?
2. iOS 17.0+ Deployment Target
3. Simulator verfügbar: `xcrun simctl list devices`

## 🚧 Roadmap

- [ ] **Echte API Integration**: Firecrawl für Live-Daten
- [ ] **Authentifizierung**: User Accounts & Favoriten
- [ ] **Push Notifications**: Preisalarme
- [ ] **Offline Support**: Lokale Datenbankintegration
- [ ] **Erweiterte Filter**: Marke, Bio, etc.
- [ ] **Barcode Scanner**: Produkterkennung per Kamera
- [ ] **Preisverlauf**: Historische Preisdaten
- [ ] **Shopping Liste**: Einkaufslistenerstellung

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen: `git checkout -b feature/amazing-feature`
3. Änderungen committen: `git commit -m 'Add amazing feature'`
4. Branch pushen: `git push origin feature/amazing-feature`
5. Pull Request erstellen

## 📄 Lizenz

Dieses Projekt steht unter der MIT Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 👨‍💻 Entwickler

Erstellt mit ❤️ für den deutschen Markt.

---

**Hinweis**: Diese App verwendet derzeit Mock-Daten für Demonstrationszwecke. Für Produktivumgebung sollte die Firecrawl-Integration aktiviert werden.
