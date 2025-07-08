package com.preisvergleich.android.feature.search

import com.preisvergleich.android.data.model.Store
import com.preisvergleich.android.data.model.ProductResult
import java.math.BigDecimal

// UI-State für die Suche und Filter

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
    val searchResults: List<ProductResult> = emptyList()
) 