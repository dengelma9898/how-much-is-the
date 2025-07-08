package com.preisvergleich.android.data.repository

import com.preisvergleich.android.data.model.SearchRequest
import com.preisvergleich.android.data.model.SearchResponse
import com.preisvergleich.android.data.model.StoresResponse
import com.preisvergleich.android.data.network.ApiService
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SearchRepositoryImpl @Inject constructor(
    private val apiService: ApiService
) : SearchRepository {
    
    override suspend fun searchProducts(request: SearchRequest): SearchResponse {
        return apiService.searchProducts(request)
    }
    
    override suspend fun getStores(): StoresResponse {
        return apiService.getStores()
    }
} 