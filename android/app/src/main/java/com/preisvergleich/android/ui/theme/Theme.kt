package com.preisvergleich.android.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Colors inspired by the app icon
private val Green50 = Color(0xFFE8F5E8)
private val Green100 = Color(0xFFC8E6C9)
private val Green200 = Color(0xFFA5D6A7)
private val Green300 = Color(0xFF81C784)
private val Green400 = Color(0xFF66BB6A)
private val Green500 = Color(0xFF4CAF50)
private val Green600 = Color(0xFF43A047)
private val Green700 = Color(0xFF388E3C)
private val Green800 = Color(0xFF2E7D32)
private val Green900 = Color(0xFF1B5E20)

private val Yellow50 = Color(0xFFFFFDE7)
private val Yellow100 = Color(0xFFFFF9C4)
private val Yellow200 = Color(0xFFFFF59D)
private val Yellow300 = Color(0xFFFFF176)
private val Yellow400 = Color(0xFFFFEE58)
private val Yellow500 = Color(0xFFFFEB3B)
private val Yellow600 = Color(0xFFFDD835)
private val Yellow700 = Color(0xFFFBC02D)
private val Yellow800 = Color(0xFFF9A825)
private val Yellow900 = Color(0xFFF57F17)

private val LightColorScheme = lightColorScheme(
    primary = Green500,
    onPrimary = Color.White,
    primaryContainer = Green100,
    onPrimaryContainer = Green900,
    
    secondary = Green300,
    onSecondary = Color.White,
    secondaryContainer = Green50,
    onSecondaryContainer = Green800,
    
    tertiary = Yellow600,
    onTertiary = Color.Black,
    tertiaryContainer = Yellow100,
    onTertiaryContainer = Yellow900,
    
    background = Color(0xFFFCFDF6),
    onBackground = Color(0xFF1A1C18),
    surface = Color(0xFFFCFDF6),
    onSurface = Color(0xFF1A1C18),
    surfaceVariant = Color(0xFFDFE4D7),
    onSurfaceVariant = Color(0xFF43483F),
    
    error = Color(0xFFBA1A1A),
    onError = Color.White,
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF410002),
    
    outline = Color(0xFF73796E),
    outlineVariant = Color(0xFFC3C8BC)
)

private val DarkColorScheme = darkColorScheme(
    primary = Green200,
    onPrimary = Green900,
    primaryContainer = Green700,
    onPrimaryContainer = Green100,
    
    secondary = Green300,
    onSecondary = Green800,
    secondaryContainer = Green600,
    onSecondaryContainer = Green50,
    
    tertiary = Yellow300,
    onTertiary = Yellow900,
    tertiaryContainer = Yellow700,
    onTertiaryContainer = Yellow100,
    
    background = Color(0xFF1A1C18),
    onBackground = Color(0xFFE3E3DD),
    surface = Color(0xFF1A1C18),
    onSurface = Color(0xFFE3E3DD),
    surfaceVariant = Color(0xFF43483F),
    onSurfaceVariant = Color(0xFFC3C8BC),
    
    error = Color(0xFFFFB4AB),
    onError = Color(0xFF690005),
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    
    outline = Color(0xFF8D9387),
    outlineVariant = Color(0xFF43483F)
)

@Composable
fun PreisvergleichTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) {
        DarkColorScheme
    } else {
        LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
} 