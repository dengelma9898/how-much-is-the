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
    onPostalCodeChange: (String) -> Unit,
    onClose: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        Text("Supermärkte filtern", style = MaterialTheme.typography.titleMedium)
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.horizontalScroll(rememberScrollState())
        ) {
            uiState.stores.forEach { store ->
                val selected = uiState.selectedStores.contains(store.id)
                FilterChip(
                    selected = selected,
                    onClick = {
                        val newList = uiState.selectedStores.toMutableList()
                        if (selected) newList.remove(store.id) else newList.add(store.id)
                        onSelectedStoresChange(newList)
                    },
                    label = { Text(store.name) },
                    leadingIcon = {
                        // Optional: Store-Logo als Icon
                    },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = MaterialTheme.colorScheme.primaryContainer
                    )
                )
            }
        }
        
        // Postleitzahl
        OutlinedTextField(
            value = uiState.postalCode,
            onValueChange = onPostalCodeChange,
            label = { Text("Postleitzahl") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth(),
            supportingText = { Text("Ihre aktuelle Postleitzahl für lokale Angebote") }
        )
        
        // Einheit
        OutlinedTextField(
            value = uiState.unit ?: "",
            onValueChange = { onUnitChange(it.ifBlank { null }) },
            label = { Text("Einheit (optional)") },
            modifier = Modifier.fillMaxWidth()
        )
        // Maximalpreis
        Column {
            Text("Maximalpreis (optional)")
            Row(verticalAlignment = Alignment.CenterVertically) {
                Slider(
                    value = (uiState.maxPrice?.toFloat() ?: 10f).coerceIn(0f, 10f),
                    onValueChange = { onMaxPriceChange(it.toBigDecimal()) },
                    valueRange = 0f..10f,
                    steps = 99,
                    modifier = Modifier.weight(1f)
                )
                Spacer(Modifier.width(8.dp))
                OutlinedTextField(
                    value = uiState.maxPrice?.toPlainString() ?: "",
                    onValueChange = {
                        onMaxPriceChange(it.toBigDecimalOrNull())
                    },
                    label = { Text("€") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    singleLine = true,
                    modifier = Modifier.width(80.dp)
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