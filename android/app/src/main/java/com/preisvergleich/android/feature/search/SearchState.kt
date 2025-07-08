package com.preisvergleich.android.feature.search

import com.preisvergleich.android.data.model.Store
import com.preisvergleich.android.data.model.ProductResult
import java.math.BigDecimal
import java.util.UUID

// UI-State für die Suche und Filter

data class SavedSearch(
    val id: String = UUID.randomUUID().toString(),
    val name: String, // Anzeigename für die gespeicherte Suche
    val query: String,
    val postalCode: String,
    val selectedStores: List<String> = emptyList(),
    val unit: String? = null,
    val maxPrice: BigDecimal? = null,
    val createdAt: Long = System.currentTimeMillis()
)

data class SearchUiState(
    val query: String = "",
    val postalCode: String = "",
    val selectedStores: List<String> = emptyList(),
    val unit: String? = null,
    val maxPrice: BigDecimal? = null,
    val isFilterSheetOpen: Boolean = false,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val stores: List<Store> = emptyList(),
    val searchResults: List<ProductResult> = emptyList(),
    val savedSearches: List<SavedSearch> = emptyList(),
    val filtersEnabled: Boolean = true, // Toggle zum Ein-/Ausschalten aller Filter (außer PLZ)
    val showSaveButton: Boolean = false // Zeigt Save-Button nach erfolgreicher Suche
) 