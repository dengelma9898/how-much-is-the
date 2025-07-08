package com.preisvergleich.android.data.network

import com.preisvergleich.android.data.model.SearchRequest
import com.preisvergleich.android.data.model.SearchResponse
import com.preisvergleich.android.data.model.StoresResponse
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface ApiService {
    @POST("api/v1/search")
    suspend fun searchProducts(@Body request: SearchRequest): SearchResponse
    
    @GET("api/v1/stores")
    suspend fun getStores(): StoresResponse
} 