package com.preisvergleich.android.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.preisvergleich.android.feature.search.SearchScreen

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PreisvergleichApp() {
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