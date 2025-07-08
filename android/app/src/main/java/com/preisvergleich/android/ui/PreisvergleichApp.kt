package com.preisvergleich.android.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import com.preisvergleich.android.feature.onboarding.OnboardingScreen
import com.preisvergleich.android.feature.onboarding.PostalCodeSetupScreen
import com.preisvergleich.android.feature.search.SearchScreen

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PreisvergleichApp(
    viewModel: AppViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()

    when {
        state.isLoading -> {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        }
        state.currentDestination is AppDestination.Onboarding -> {
            OnboardingScreen(
                onComplete = viewModel::completeOnboarding
            )
        }
        state.currentDestination is AppDestination.PostalCodeSetup -> {
            PostalCodeSetupScreen(
                onPostalCodeSaved = viewModel::savePostalCode
            )
        }
        state.currentDestination is AppDestination.Main -> {
            Scaffold(
                topBar = {
                    TopAppBar(
                        title = { Text("Preisvergleich") }
                    )
                }
            ) { paddingValues ->
                SearchScreen(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                )
            }
        }
    }
} 