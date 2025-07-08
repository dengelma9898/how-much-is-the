package com.preisvergleich.android.feature.search

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import java.math.BigDecimal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(
    viewModel: SearchViewModel = hiltViewModel(),
    modifier: Modifier = Modifier,
    initialPostalCode: String? = null,
    onPostalCodeChanged: (String) -> Unit = {}
) {
    // Initialize postal code when screen is first composed
    LaunchedEffect(initialPostalCode) {
        initialPostalCode?.let { 
            viewModel.onPostalCodeChange(it)
        }
    }
    val uiState by viewModel.uiState.collectAsState()
    val focusManager = LocalFocusManager.current
    val filterActive = uiState.selectedStores.isNotEmpty() || uiState.unit != null || uiState.maxPrice != null
    val filterIconScale by animateFloatAsState(targetValue = if (uiState.isFilterSheetOpen) 1.15f else 1f, label = "filterIconScale")
    
    Box(modifier = modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // App Header
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                ),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // App icon placeholder (will show your green icon)
                    Box(
                        modifier = Modifier
                            .size(48.dp)
                            .background(
                                MaterialTheme.colorScheme.primary,
                                shape = RoundedCornerShape(12.dp)
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "🛒",
                            style = MaterialTheme.typography.headlineMedium
                        )
                    }
                    
                    Column {
                        Text(
                            text = "Preisvergleich",
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                        Text(
                            text = "Finden Sie die besten Preise",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                        )
                    }
                }
            }
            // Suchfeld + Filter-Icon
            Row(verticalAlignment = Alignment.Bottom) {
                OutlinedTextField(
                    value = uiState.query,
                    onValueChange = viewModel::onQueryChange,
                    label = { Text("Was suchen Sie?") },
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                    keyboardOptions = KeyboardOptions.Default.copy(imeAction = ImeAction.Search),
                    keyboardActions = KeyboardActions(
                        onSearch = {
                            focusManager.clearFocus()
                            viewModel.search()
                        }
                    ),
                    trailingIcon = {
                        Box {
                            IconButton(
                                onClick = { viewModel.openFilterSheet(true) },
                                modifier = Modifier
                                    .scale(filterIconScale)
                                    .background(
                                        if (filterActive) MaterialTheme.colorScheme.primary.copy(alpha = 0.15f) else Color.Transparent,
                                        shape = CircleShape
                                    )
                            ) {
                                Icon(
                                    imageVector = Icons.Default.FilterList,
                                    contentDescription = "Filter",
                                    tint = if (filterActive) MaterialTheme.colorScheme.primary else Color.Gray
                                )
                            }
                            if (filterActive) {
                                Box(
                                    modifier = Modifier
                                        .size(10.dp)
                                        .background(Color.Red, shape = CircleShape)
                                        .align(Alignment.TopEnd)
                                )
                            }
                        }
                    }
                )
            }

            // Suche-Button
            Button(
                onClick = { 
                    focusManager.clearFocus()
                    viewModel.search()
                },
                enabled = uiState.query.isNotBlank() && !uiState.isLoading,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Preise vergleichen")
            }
            // Fehler
            if (uiState.errorMessage != null) {
                Text(uiState.errorMessage!!, color = MaterialTheme.colorScheme.error)
            }
            // Ladeanzeige
            if (uiState.isLoading) {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.CenterHorizontally))
            }
            // Ergebnisliste
            if (!uiState.isLoading && uiState.errorMessage == null) {
                if (uiState.searchResults.isNotEmpty()) {
                    ProductResultList(results = uiState.searchResults)
                } else {
                    // Leerer Zustand
                    Column(
                        modifier = Modifier.fillMaxWidth().padding(top = 32.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(
                            imageVector = Icons.Default.FilterList,
                            contentDescription = null,
                            tint = Color.Gray,
                            modifier = Modifier.size(48.dp)
                        )
                        Text(
                            text = if (uiState.query.isBlank()) "Geben Sie einen Suchbegriff ein" else "Keine Ergebnisse gefunden",
                            color = Color.Gray
                        )
                    }
                }
            }
        }
        // Filter-BottomSheet
        if (uiState.isFilterSheetOpen) {
            ModalBottomSheet(
                onDismissRequest = { viewModel.openFilterSheet(false) },
                dragHandle = { BottomSheetDefaults.DragHandle() },
                sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
            ) {
                SearchFilterSheet(
                    uiState = uiState,
                    onSelectedStoresChange = viewModel::onSelectedStoresChange,
                    onUnitChange = viewModel::onUnitChange,
                    onMaxPriceChange = viewModel::onMaxPriceChange,
                    onPostalCodeChange = { newValue ->
                        viewModel.onPostalCodeChange(newValue)
                        onPostalCodeChanged(newValue)
                    },
                    onClose = { viewModel.openFilterSheet(false) }
                )
            }
        }
    }
} 