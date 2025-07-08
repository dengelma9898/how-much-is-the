package com.preisvergleich.android.feature.onboarding

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PostalCodeSetupScreen(
    onPostalCodeSaved: (String) -> Unit
) {
    var postalCode by remember { mutableStateOf("") }
    var isError by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Icon
        Box(
            modifier = Modifier
                .size(100.dp)
                .background(
                    MaterialTheme.colorScheme.primaryContainer,
                    RoundedCornerShape(50.dp)
                ),
            contentAlignment = Alignment.Center
        ) {
            Text("📍", fontSize = 48.sp)
        }

        Spacer(modifier = Modifier.height(32.dp))

        // Title
        Text(
            text = "Ihre Postleitzahl",
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onBackground,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Description
        Text(
            text = "Geben Sie Ihre Postleitzahl ein, um lokale Angebote und Supermärkte in Ihrer Nähe zu finden.",
            fontSize = 16.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            lineHeight = 24.sp
        )

        Spacer(modifier = Modifier.height(48.dp))

        // Postal Code Input
        OutlinedTextField(
            value = postalCode,
            onValueChange = { newValue ->
                // Only allow digits and limit to 5 characters
                if (newValue.all { it.isDigit() } && newValue.length <= 5) {
                    postalCode = newValue
                    isError = false
                }
            },
            label = { Text("Postleitzahl") },
            placeholder = { Text("z.B. 10115") },
            isError = isError,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            singleLine = true,
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp)
        )

        if (isError) {
            Text(
                text = "Bitte geben Sie eine gültige 5-stellige Postleitzahl ein",
                color = MaterialTheme.colorScheme.error,
                fontSize = 12.sp,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
            )
        }

        Spacer(modifier = Modifier.height(32.dp))

        // Continue Button
        Button(
            onClick = {
                if (postalCode.length == 5) {
                    onPostalCodeSaved(postalCode)
                } else {
                    isError = true
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
                .padding(horizontal = 16.dp),
            shape = RoundedCornerShape(28.dp),
            enabled = postalCode.isNotEmpty()
        ) {
            Text(
                text = "Weiter",
                fontSize = 18.sp,
                fontWeight = FontWeight.Medium
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Skip option
        TextButton(
            onClick = { onPostalCodeSaved("") }
        ) {
            Text(
                text = "Später eingeben",
                color = MaterialTheme.colorScheme.outline
            )
        }
    }
} 