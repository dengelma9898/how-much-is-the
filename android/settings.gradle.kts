pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        // WICHTIG: mavenCentral() muss vor google() stehen, da Coil Compose nur dort verfügbar ist
        mavenCentral()
        google()
    }
}

rootProject.name = "PreisvergleichAndroid"
include(":app") 