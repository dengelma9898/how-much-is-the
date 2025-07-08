# Preisvergleich Android App

Eine moderne Android-App für Preisvergleiche in deutschen Supermärkten, entwickelt mit Kotlin und Jetpack Compose.

## 🚀 Features

- **Modern UI** mit Jetpack Compose und Material3
- **MVVM Architecture** mit ViewModels und State Management
- **Reactive Programming** mit Coroutines und Flow
- **Network Layer** mit Retrofit und OkHttp
- **Local Storage** mit Room Database und DataStore
- **Dependency Injection** mit Hilt
- **Image Loading** mit Coil
- **Type-Safe Navigation** mit Navigation Compose

## 🛠️ Tech Stack

| Kategorie | Technologie | Version |
|-----------|-------------|---------|
| Language | Kotlin | 2.1.0 |
| UI Framework | Jetpack Compose | 2024.12.01 |
| Architecture | MVVM + Clean Architecture | - |
| DI | Hilt | 2.53 |
| Network | Retrofit + OkHttp | 2.11.0 |
| Database | Room | 2.6.1 |
| Image Loading | Coil | 2.8.0 |
| Navigation | Navigation Compose | 2.8.4 |

## 📁 Projektstruktur

```
app/src/main/java/com/preisvergleich/android/
├── data/
│   ├── model/          # Datenmodelle
│   ├── network/        # API Services
│   ├── local/          # Room Database
│   └── repository/     # Repository Pattern
├── domain/
│   ├── model/          # Domain Models
│   ├── repository/     # Repository Interfaces
│   └── usecase/        # Business Logic
├── presentation/
│   ├── ui/
│   │   ├── theme/      # Material3 Theme
│   │   ├── screens/    # Compose Screens
│   │   └── components/ # Reusable Components
│   └── viewmodel/      # ViewModels
├── di/                 # Hilt Modules
└── util/              # Utilities
```

## 🏗️ Setup

### Voraussetzungen
- Android Studio Giraffe oder neuer
- JDK 11 oder neuer
- Android SDK 24+ (Android 7.0)

### Installation

1. **Repository klonen**
```bash
git clone <repository-url>
cd android
```

2. **Dependencies installieren**
```bash
./gradlew build
```

3. **Backend starten**
```bash
cd ../backend
uvicorn app.main:app --reload
```

4. **App in Android Studio öffnen**
- Öffne das `android` Verzeichnis in Android Studio
- Synce Gradle Files
- Starte die App mit ▶️

## 🎨 UI/UX Design

### Material Design 3
- **Dynamic Color** Support
- **Dark/Light Theme** Unterstützung
- **Adaptive Layouts** für verschiedene Bildschirmgrößen
- **Accessibility** Features (TalkBack, Large Text)

### Screens
1. **Onboarding Screen** - Postleitzahl-Eingabe
2. **Search Screen** - Produktsuche mit Suchleiste
3. **Results Screen** - Produktliste mit Preisen
4. **Product Detail** - Detailansicht eines Produkts
5. **Settings Screen** - App-Einstellungen

## 🏛️ Architektur

### MVVM Pattern
```
View (Compose) → ViewModel → Repository → DataSource
```

### Clean Architecture Layers
1. **Presentation Layer** - UI Components & ViewModels
2. **Domain Layer** - Business Logic & Use Cases
3. **Data Layer** - Repositories & Data Sources

### State Management
- `@StateOf` für lokale UI-States
- `StateFlow` für ViewModel-States
- `Flow` für Datenstreams
- `Compose State` für UI-Reaktivität

## 🌐 API Integration

### Base URL
```kotlin
const val BASE_URL = "http://10.0.2.2:8000/api/v1/" // Android Emulator
```

### Endpunkte
- `POST /search` - Produktsuche
- `GET /stores` - Verfügbare Supermärkte
- `GET /health` - API Health Check

### Error Handling
```kotlin
sealed class ApiResult<T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error<T>(val exception: Throwable) : ApiResult<T>()
    class Loading<T> : ApiResult<T>()
}
```

## 💾 Datenspeicherung

### Room Database
```kotlin
@Entity(tableName = "search_history")
data class SearchHistoryEntity(
    @PrimaryKey val id: String,
    val query: String,
    val timestamp: Long
)
```

### DataStore Preferences
```kotlin
val POSTAL_CODE_KEY = stringPreferencesKey("postal_code")
```

## 🧪 Testing

### Unit Tests
```bash
./gradlew testDebugUnitTest
```

### Instrumented Tests
```bash
./gradlew connectedAndroidTest
```

### UI Tests mit Compose
```kotlin
@Test
fun searchScreen_displaysResults() {
    composeTestRule.setContent {
        SearchScreen(/* ... */)
    }
    composeTestRule.onNodeWithText("Oatly").assertIsDisplayed()
}
```

## 🚀 Build & Deploy

### Debug Build
```bash
./gradlew assembleDebug
```

### Release Build
```bash
./gradlew assembleRelease
```

### Code Quality
```bash
./gradlew ktlintCheck  # Kotlin Linting
./gradlew detekt       # Static Analysis
```

## 📋 TODO

- [ ] Offline-Modus mit lokaler Datenbank
- [ ] Push-Notifications für Preisalarme
- [ ] Biometrische Authentifizierung
- [ ] Widget für Homescreen
- [ ] App Shortcuts
- [ ] Performance Optimierung
- [ ] Analytics Integration

## 🔧 Konfiguration

### Gradle Properties
```properties
# gradle.properties
org.gradle.jvmargs=-Xmx2048m
org.gradle.parallel=true
kotlin.code.style=official
```

### Proguard Rules
```proguard
# app/proguard-rules.pro
-keep class com.preisvergleich.android.data.model.** { *; }
-dontwarn retrofit2.**
```

## 🐛 Debugging

### Logging
```kotlin
private val logger = Logger.getLogger(SearchViewModel::class.java.name)

logger.info("Search started for query: $query")
```

### Network Debugging
- OkHttp Logging Interceptor aktiviert in Debug-Builds
- Stetho für Network Inspector (optional)

## 📱 Kompatibilität

- **Minimum SDK**: 24 (Android 7.0)
- **Target SDK**: 35 (Android 15)
- **Supported Architectures**: arm64-v8a, armeabi-v7a, x86_64

## 🤝 Contributing

1. Feature Branch erstellen
2. Code Style Guidelines befolgen
3. Tests schreiben
4. Pull Request erstellen

---

**Happy Coding! 🚀** 