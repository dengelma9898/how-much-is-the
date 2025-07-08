package com.preisvergleich.android.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import java.math.BigDecimal

@Serializable
data class SearchRequest(
    val query: String,
    @SerialName("postal_code")
    val postalCode: String,
    @SerialName("selected_stores")
    val selectedStores: List<String>? = null,
    val unit: String? = null,
    @SerialName("max_price")
    @Serializable(with = BigDecimalSerializer::class)
    val maxPrice: BigDecimal? = null
)

@Serializable
data class ProductResult(
    val name: String,
    @Serializable(with = BigDecimalSerializer::class)
    val price: BigDecimal,
    val store: String,
    @SerialName("store_logo_url")
    val storeLogoUrl: String? = null,
    @SerialName("product_url")
    val productUrl: String? = null,
    @SerialName("image_url")
    val imageUrl: String? = null,
    val availability: String = "verfügbar",
    val unit: String? = null,
    @SerialName("price_per_unit")
    @Serializable(with = BigDecimalSerializer::class)
    val pricePerUnit: BigDecimal? = null
)

@Serializable
data class SearchResponse(
    val results: List<ProductResult>,
    val query: String,
    @SerialName("postal_code")
    val postalCode: String,
    @SerialName("total_results")
    val totalResults: Int,
    @SerialName("search_time_ms")
    val searchTimeMs: Int
)

@Serializable
data class Store(
    val id: String,
    val name: String,
    @SerialName("logo_url")
    val logoUrl: String? = null,
    @SerialName("website_url")
    val websiteUrl: String? = null,
    val category: String
)

@Serializable
data class StoresResponse(
    val stores: List<Store>
) 