package com.preisvergleich.android.feature.search

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.preisvergleich.android.data.model.Store
import java.math.BigDecimal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchFilterSheet(
    uiState: SearchUiState,
    onSelectedStoresChange: (List<String>) -> Unit,
    onUnitChange: (String?) -> Unit,
    onMaxPriceChange: (BigDecimal?) -> Unit,
    onFiltersToggle: (Boolean) -> Unit,
    onClose: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        // Filter Toggle
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text("Filter aktivieren", style = MaterialTheme.typography.titleMedium)
                Text(
                    text = if (uiState.filtersEnabled) "Filter werden angewendet" else "Nur Suchbegriff wird verwendet",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Switch(
                checked = uiState.filtersEnabled,
                onCheckedChange = onFiltersToggle
            )
        }
        
        HorizontalDivider()
        
        // Stores Filter - ausgegraut wenn Filter deaktiviert
        Text(
            "Supermärkte filtern", 
            style = MaterialTheme.typography.titleMedium,
            color = if (uiState.filtersEnabled) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant
        )
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.horizontalScroll(rememberScrollState())
        ) {
            uiState.stores.forEach { store ->
                val selected = uiState.selectedStores.contains(store.id)
                FilterChip(
                    selected = selected && uiState.filtersEnabled,
                    onClick = {
                        if (uiState.filtersEnabled) {
                            val newList = uiState.selectedStores.toMutableList()
                            if (selected) newList.remove(store.id) else newList.add(store.id)
                            onSelectedStoresChange(newList)
                        }
                    },
                    label = { Text(store.name) },
                    leadingIcon = {
                        // Optional: Store-Logo als Icon
                    },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = if (uiState.filtersEnabled) 
                            MaterialTheme.colorScheme.primaryContainer 
                        else 
                            MaterialTheme.colorScheme.surfaceVariant
                    ),
                    enabled = uiState.filtersEnabled
                )
            }
        }
        
        // Einheit - ausgegraut wenn Filter deaktiviert
        OutlinedTextField(
            value = if (uiState.filtersEnabled) (uiState.unit ?: "") else "",
            onValueChange = { 
                if (uiState.filtersEnabled) {
                    onUnitChange(it.ifBlank { null })
                }
            },
            label = { Text("Einheit (optional)") },
            modifier = Modifier.fillMaxWidth(),
            enabled = uiState.filtersEnabled,
            colors = OutlinedTextFieldDefaults.colors(
                disabledLabelColor = MaterialTheme.colorScheme.onSurfaceVariant,
                disabledBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.3f)
            )
        )
        
        // Maximalpreis - ausgegraut wenn Filter deaktiviert
        Column {
            Text(
                "Maximalpreis (optional)",
                color = if (uiState.filtersEnabled) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant
            )
            Row(verticalAlignment = Alignment.CenterVertically) {
                Slider(
                    value = if (uiState.filtersEnabled) (uiState.maxPrice?.toFloat() ?: 10f).coerceIn(0f, 10f) else 10f,
                    onValueChange = { 
                        if (uiState.filtersEnabled) {
                            onMaxPriceChange(it.toBigDecimal())
                        }
                    },
                    valueRange = 0f..10f,
                    steps = 99,
                    modifier = Modifier.weight(1f),
                    enabled = uiState.filtersEnabled
                )
                Spacer(Modifier.width(8.dp))
                OutlinedTextField(
                    value = if (uiState.filtersEnabled) (uiState.maxPrice?.toPlainString() ?: "") else "",
                    onValueChange = {
                        if (uiState.filtersEnabled) {
                            onMaxPriceChange(it.toBigDecimalOrNull())
                        }
                    },
                    label = { Text("€") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    singleLine = true,
                    modifier = Modifier.width(80.dp),
                    enabled = uiState.filtersEnabled,
                    colors = OutlinedTextFieldDefaults.colors(
                        disabledLabelColor = MaterialTheme.colorScheme.onSurfaceVariant,
                        disabledBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.3f)
                    )
                )
            }
        }
        Spacer(Modifier.height(8.dp))
        Button(
            onClick = onClose,
            modifier = Modifier.align(Alignment.End)
        ) {
            Text("Fertig")
        }
    }
}

private fun String.toBigDecimalOrNull(): BigDecimal? =
    try { BigDecimal(this.replace(',', '.')) } catch (_: Exception) { null } 