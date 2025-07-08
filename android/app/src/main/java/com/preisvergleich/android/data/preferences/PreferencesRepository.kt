package com.preisvergleich.android.data.preferences

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "app_preferences")

@Singleton
class PreferencesRepository @Inject constructor(
    private val context: Context
) {
    private val dataStore = context.dataStore

    companion object {
        private val POSTAL_CODE_KEY = stringPreferencesKey("postal_code")
        private val INTRO_COMPLETED_KEY = booleanPreferencesKey("intro_completed")
    }

    val postalCode: Flow<String?> = dataStore.data.map { preferences ->
        preferences[POSTAL_CODE_KEY]
    }

    val isIntroCompleted: Flow<Boolean> = dataStore.data.map { preferences ->
        preferences[INTRO_COMPLETED_KEY] ?: false
    }

    suspend fun savePostalCode(postalCode: String) {
        dataStore.edit { preferences ->
            preferences[POSTAL_CODE_KEY] = postalCode
        }
    }

    suspend fun setIntroCompleted() {
        dataStore.edit { preferences ->
            preferences[INTRO_COMPLETED_KEY] = true
        }
    }

    suspend fun clearAllPreferences() {
        dataStore.edit { preferences ->
            preferences.clear()
        }
    }
} 