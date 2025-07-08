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
import android.content.Context
import android.content.SharedPreferences
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.Serializable

@Serializable
data class SavedSearchData(
    val id: String,
    val name: String,
    val query: String,
    val postalCode: String,
    val selectedStores: List<String>,
    val unit: String?,
    val maxPrice: String?, // Als String für Serialization
    val createdAt: Long
)

@HiltViewModel
class SearchViewModel @Inject constructor(
    private val searchRepository: SearchRepository,
    @ApplicationContext private val context: Context
) : ViewModel() {
    private val _uiState = MutableStateFlow(SearchUiState())
    val uiState: StateFlow<SearchUiState> = _uiState.asStateFlow()
    
    private val sharedPreferences: SharedPreferences = 
        context.getSharedPreferences("saved_searches", Context.MODE_PRIVATE)

    init {
        loadStores()
        loadSavedSearches()
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
    
    private fun loadSavedSearches() {
        try {
            val savedSearchesJson = sharedPreferences.getString("searches", null)
            if (savedSearchesJson != null) {
                val savedSearchData: List<SavedSearchData> = Json.decodeFromString(savedSearchesJson)
                val savedSearches = savedSearchData.map { data ->
                    SavedSearch(
                        id = data.id,
                        name = data.name,
                        query = data.query,
                        postalCode = data.postalCode,
                        selectedStores = data.selectedStores,
                        unit = data.unit,
                        maxPrice = data.maxPrice?.let { BigDecimal(it) },
                        createdAt = data.createdAt
                    )
                }
                _uiState.value = _uiState.value.copy(savedSearches = savedSearches)
            }
        } catch (e: Exception) {
            // Handle parsing errors gracefully
        }
    }
    
    private fun saveSavedSearches() {
        try {
            val savedSearchData = _uiState.value.savedSearches.map { search ->
                SavedSearchData(
                    id = search.id,
                    name = search.name,
                    query = search.query,
                    postalCode = search.postalCode,
                    selectedStores = search.selectedStores,
                    unit = search.unit,
                    maxPrice = search.maxPrice?.toPlainString(),
                    createdAt = search.createdAt
                )
            }
            val json = Json.encodeToString(savedSearchData)
            sharedPreferences.edit().putString("searches", json).apply()
        } catch (e: Exception) {
            // Handle serialization errors gracefully
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
    
    fun toggleFilters(enabled: Boolean) {
        _uiState.value = _uiState.value.copy(filtersEnabled = enabled)
    }
    
    fun hideSaveButton() {
        _uiState.value = _uiState.value.copy(showSaveButton = false)
    }

    fun search() {
        val currentState = _uiState.value
        if (currentState.query.isBlank()) return

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = true,
                searchResults = emptyList(),
                errorMessage = null,
                showSaveButton = false
            )
            
            try {
                val searchRequest = SearchRequest(
                    query = currentState.query,
                    postalCode = currentState.postalCode.ifBlank { "90402" }, // Default postal code
                    selectedStores = if (currentState.filtersEnabled) currentState.selectedStores.ifEmpty { null } else null,
                    unit = if (currentState.filtersEnabled) currentState.unit else null,
                    maxPrice = if (currentState.filtersEnabled) currentState.maxPrice else null
                )
                
                val searchResponse = searchRepository.searchProducts(searchRequest)
                
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    searchResults = searchResponse.results,
                    showSaveButton = searchResponse.results.isNotEmpty()
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    searchResults = emptyList(),
                    errorMessage = "Fehler beim Laden der Suchergebnisse: ${e.message}",
                    showSaveButton = false
                )
            }
        }
    }
    
    fun saveCurrentSearch(name: String) {
        val currentState = _uiState.value
        if (currentState.query.isBlank()) return
        
        val newSearch = SavedSearch(
            name = name.ifBlank { currentState.query }, // Fallback auf query wenn kein Name
            query = currentState.query,
            postalCode = currentState.postalCode.ifBlank { "90402" },
            selectedStores = currentState.selectedStores,
            unit = currentState.unit,
            maxPrice = currentState.maxPrice
        )
        
        val updatedSearches = _uiState.value.savedSearches + newSearch
        _uiState.value = _uiState.value.copy(
            savedSearches = updatedSearches,
            showSaveButton = false
        )
        saveSavedSearches()
    }
    
    fun loadSavedSearch(savedSearch: SavedSearch) {
        _uiState.value = _uiState.value.copy(
            query = savedSearch.query,
            postalCode = savedSearch.postalCode,
            selectedStores = if (_uiState.value.filtersEnabled) savedSearch.selectedStores else emptyList(),
            unit = if (_uiState.value.filtersEnabled) savedSearch.unit else null,
            maxPrice = if (_uiState.value.filtersEnabled) savedSearch.maxPrice else null
        )
        // Automatisch suchen nach dem Laden
        search()
    }
    
    fun deleteSavedSearch(searchId: String) {
        val updatedSearches = _uiState.value.savedSearches.filter { it.id != searchId }
        _uiState.value = _uiState.value.copy(savedSearches = updatedSearches)
        saveSavedSearches()
    }
} 