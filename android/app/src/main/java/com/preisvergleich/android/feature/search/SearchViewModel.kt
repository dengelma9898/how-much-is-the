package com.preisvergleich.android.feature.search

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.preisvergleich.android.data.model.SearchRequest
import com.preisvergleich.android.data.model.Store
import com.preisvergleich.android.data.repository.SearchRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.math.BigDecimal
import javax.inject.Inject

@HiltViewModel
class SearchViewModel @Inject constructor(
    private val searchRepository: SearchRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(SearchUiState())
    val uiState: StateFlow<SearchUiState> = _uiState.asStateFlow()

    init {
        loadStores()
    }

    private fun loadStores() {
        viewModelScope.launch {
            try {
                val storesResponse = searchRepository.getStores()
                _uiState.value = _uiState.value.copy(stores = storesResponse.stores)
            } catch (e: Exception) {
                // Use mock data as fallback
                _uiState.value = _uiState.value.copy(
                    stores = listOf(
                        Store("rewe", "REWE", null, null, "Supermarkt"),
                        Store("aldi", "ALDI", null, null, "Discounter"),
                        Store("lidl", "Lidl", null, null, "Discounter")
                    )
                )
            }
        }
    }

    fun onQueryChange(query: String) {
        _uiState.value = _uiState.value.copy(query = query)
    }
    fun onPostalCodeChange(postalCode: String) {
        _uiState.value = _uiState.value.copy(postalCode = postalCode)
    }
    fun onSelectedStoresChange(stores: List<String>) {
        _uiState.value = _uiState.value.copy(selectedStores = stores)
    }
    fun onUnitChange(unit: String?) {
        _uiState.value = _uiState.value.copy(unit = unit)
    }
    fun onMaxPriceChange(maxPrice: BigDecimal?) {
        _uiState.value = _uiState.value.copy(maxPrice = maxPrice)
    }
    fun openFilterSheet(open: Boolean) {
        _uiState.value = _uiState.value.copy(isFilterSheetOpen = open)
    }
    fun setError(message: String?) {
        _uiState.value = _uiState.value.copy(errorMessage = message)
    }
    fun setLoading(loading: Boolean) {
        _uiState.value = _uiState.value.copy(isLoading = loading)
    }

    fun search() {
        val currentState = _uiState.value
        if (currentState.query.isBlank()) return

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = true,
                searchResults = emptyList(),
                errorMessage = null
            )
            
            try {
                val searchRequest = SearchRequest(
                    query = currentState.query,
                    postalCode = currentState.postalCode.ifBlank { "90402" }, // Default postal code
                    selectedStores = currentState.selectedStores.ifEmpty { null },
                    unit = currentState.unit,
                    maxPrice = currentState.maxPrice
                )
                
                val searchResponse = searchRepository.searchProducts(searchRequest)
                
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    searchResults = searchResponse.results
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    searchResults = emptyList(),
                    errorMessage = "Fehler beim Laden der Suchergebnisse: ${e.message}"
                )
            }
        }
    }
} 