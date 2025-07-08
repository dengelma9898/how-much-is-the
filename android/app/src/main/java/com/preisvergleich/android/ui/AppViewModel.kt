package com.preisvergleich.android.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.preisvergleich.android.data.preferences.PreferencesRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class AppDestination {
    object Onboarding : AppDestination()
    object PostalCodeSetup : AppDestination()
    object Main : AppDestination()
}

data class AppState(
    val isLoading: Boolean = true,
    val currentDestination: AppDestination = AppDestination.Onboarding,
    val postalCode: String? = null
)

@HiltViewModel
class AppViewModel @Inject constructor(
    private val preferencesRepository: PreferencesRepository
) : ViewModel() {

    private val _state = MutableStateFlow(AppState())
    val state: StateFlow<AppState> = _state.asStateFlow()

    init {
        observeAppState()
    }

    private fun observeAppState() {
        viewModelScope.launch {
            combine(
                preferencesRepository.isIntroCompleted,
                preferencesRepository.postalCode
            ) { isIntroCompleted, postalCode ->
                when {
                    !isIntroCompleted -> AppDestination.Onboarding
                    postalCode.isNullOrBlank() -> AppDestination.PostalCodeSetup
                    else -> AppDestination.Main
                }
            }.collect { destination ->
                _state.value = _state.value.copy(
                    isLoading = false,
                    currentDestination = destination,
                    postalCode = preferencesRepository.postalCode.first()
                )
            }
        }
    }

    fun completeOnboarding() {
        viewModelScope.launch {
            preferencesRepository.setIntroCompleted()
        }
    }

    fun savePostalCode(postalCode: String) {
        viewModelScope.launch {
            if (postalCode.isNotBlank()) {
                preferencesRepository.savePostalCode(postalCode)
            }
            // Navigate to main even if postal code is empty (user can set it later)
            _state.value = _state.value.copy(
                currentDestination = AppDestination.Main,
                postalCode = postalCode.ifBlank { null }
            )
        }
    }

    fun updatePostalCode(postalCode: String) {
        viewModelScope.launch {
            preferencesRepository.savePostalCode(postalCode)
            _state.value = _state.value.copy(postalCode = postalCode)
        }
    }
} 