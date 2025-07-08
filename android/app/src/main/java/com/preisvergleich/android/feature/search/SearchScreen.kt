package com.preisvergleich.android.feature.search

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.combinedClickable
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
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

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun SearchScreen(
    viewModel: SearchViewModel = hiltViewModel(),
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    val focusManager = LocalFocusManager.current
    val filterActive = uiState.selectedStores.isNotEmpty() || uiState.unit != null || uiState.maxPrice != null
    val filterIconScale by animateFloatAsState(targetValue = if (uiState.isFilterSheetOpen) 1.15f else 1f, label = "filterIconScale")
    
    // State für Save Dialog
    var showSaveDialog by remember { mutableStateOf(false) }
    var saveSearchName by remember { mutableStateOf("") }
    
    // State für Delete Dialog
    var showDeleteDialog by remember { mutableStateOf(false) }
    var searchToDelete by remember { mutableStateOf<SavedSearch?>(null) }
    
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
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Preisvergleich",
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Finden Sie die besten Angebote in Ihrer Nähe",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                    )
                }
            }
            
            // Gespeicherte Suchen
            if (uiState.savedSearches.isNotEmpty()) {
                Column {
                    Text(
                        text = "Gespeicherte Suchen",
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.horizontalScroll(rememberScrollState())
                    ) {
                        uiState.savedSearches.forEach { savedSearch ->
                            ElevatedFilterChip(
                                selected = false,
                                onClick = { viewModel.loadSavedSearch(savedSearch) },
                                label = { Text(savedSearch.name) },
                                modifier = Modifier.combinedClickable(
                                    onClick = { viewModel.loadSavedSearch(savedSearch) },
                                    onLongClick = {
                                        searchToDelete = savedSearch
                                        showDeleteDialog = true
                                    }
                                ),
                                leadingIcon = {
                                    if (!uiState.filtersEnabled) {
                                        Icon(
                                            imageVector = Icons.Default.FilterList,
                                            contentDescription = "Filter deaktiviert",
                                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                            modifier = Modifier.size(16.dp)
                                        )
                                    }
                                }
                            )
                        }
                    }
                }
            } else if (uiState.query.isNotBlank()) {
                // Hint für neue Nutzer
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                    )
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.Add,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Tipp: Klicke auf das + Symbol, um diese Suche zu speichern!",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            
            // Suchfeld mit Filter-Icon
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
                        Row {
                            // Save Icon - always visible when query is not empty
                            if (uiState.query.isNotBlank()) {
                                IconButton(
                                    onClick = {
                                        saveSearchName = uiState.query
                                        showSaveDialog = true
                                    }
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Add,
                                        contentDescription = "Suche speichern",
                                        tint = MaterialTheme.colorScheme.primary
                                    )
                                }
                            }
                            
                            // Filter Icon
                            Box {
                                IconButton(
                                    onClick = { viewModel.openFilterSheet(true) },
                                    modifier = Modifier
                                        .scale(filterIconScale)
                                        .background(
                                            if (filterActive && uiState.filtersEnabled) MaterialTheme.colorScheme.primary.copy(alpha = 0.15f) else Color.Transparent,
                                            shape = CircleShape
                                        )
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.FilterList,
                                        contentDescription = "Filter",
                                        tint = when {
                                            filterActive && uiState.filtersEnabled -> MaterialTheme.colorScheme.primary
                                            !uiState.filtersEnabled -> MaterialTheme.colorScheme.onSurfaceVariant
                                            else -> Color.Gray
                                        }
                                    )
                                }
                                if (filterActive && uiState.filtersEnabled) {
                                    Box(
                                        modifier = Modifier
                                            .size(10.dp)
                                            .background(Color.Red, shape = CircleShape)
                                            .align(Alignment.TopEnd)
                                    )
                                } else if (!uiState.filtersEnabled) {
                                    Box(
                                        modifier = Modifier
                                            .size(10.dp)
                                            .background(MaterialTheme.colorScheme.onSurfaceVariant, shape = CircleShape)
                                            .align(Alignment.TopEnd)
                                    )
                                }
                            }
                        }
                    }
                )
            }
            
            // PLZ
            OutlinedTextField(
                value = uiState.postalCode,
                onValueChange = viewModel::onPostalCodeChange,
                label = { Text("Postleitzahl") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
            )
            
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
        
        // Save Button (Floating Action Button)
        if (uiState.showSaveButton) {
            FloatingActionButton(
                onClick = {
                    saveSearchName = uiState.query // Vorausfüllen mit aktuellem Suchbegriff
                    showSaveDialog = true
                },
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(16.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Add,
                    contentDescription = "Suche speichern"
                )
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
                    onFiltersToggle = viewModel::toggleFilters,
                    onClose = { viewModel.openFilterSheet(false) }
                )
            }
        }
    }
    
    // Save Dialog
    if (showSaveDialog) {
        AlertDialog(
            onDismissRequest = { showSaveDialog = false },
            title = { Text("Suche speichern") },
            text = {
                Column {
                    Text("Geben Sie einen Namen für die gespeicherte Suche ein:")
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = saveSearchName,
                        onValueChange = { saveSearchName = it },
                        label = { Text("Name") },
                        singleLine = true
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.saveCurrentSearch(saveSearchName)
                        showSaveDialog = false
                        saveSearchName = ""
                    }
                ) {
                    Text("Speichern")
                }
            },
            dismissButton = {
                TextButton(onClick = { showSaveDialog = false }) {
                    Text("Abbrechen")
                }
            }
        )
    }
    
    // Delete Dialog
    if (showDeleteDialog && searchToDelete != null) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text("Suche löschen") },
            text = { Text("Möchten Sie die gespeicherte Suche \"${searchToDelete!!.name}\" wirklich löschen?") },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.deleteSavedSearch(searchToDelete!!.id)
                        showDeleteDialog = false
                        searchToDelete = null
                    }
                ) {
                    Text("Löschen")
                }
            },
            dismissButton = {
                TextButton(
                    onClick = { 
                        showDeleteDialog = false
                        searchToDelete = null
                    }
                ) {
                    Text("Abbrechen")
                }
            }
        )
    }
} 