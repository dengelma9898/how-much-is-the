package com.preisvergleich.android.data.repository

import com.preisvergleich.android.data.model.SearchRequest
import com.preisvergleich.android.data.model.SearchResponse
import com.preisvergleich.android.data.model.Store
import com.preisvergleich.android.data.model.StoresResponse

interface SearchRepository {
    suspend fun searchProducts(request: SearchRequest): SearchResponse
    suspend fun getStores(): StoresResponse
} 