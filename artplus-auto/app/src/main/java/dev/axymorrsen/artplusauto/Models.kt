package dev.axymorrsen.artplusauto

import android.graphics.Bitmap

internal object ArtPlusSpec {
    const val SIZE_1X1 = 240
    const val SIZE_2X2 = 704
    const val SIZE_1X2_W = 240
    const val SIZE_1X2_H = 820
    const val SIZE_2X1_W = 820
    const val SIZE_2X1_H = 240
    const val RENDER_SCALE = 3
    const val GENERATOR_VERSION = 1
}

internal enum class LayerProvenance {
    ADAPTIVE_NATIVE,
    ADAPTIVE_RECOVERED,
    LEGACY_SEPARATED,
    LEGACY_CONSERVATIVE,
}

internal data class IconLayers(
    val foreground: Bitmap,
    val background: Bitmap,
    val nativeMonochrome: Bitmap?,
    val confidence: Double,
    val provenance: LayerProvenance,
)

internal data class CompileResult(
    val packageName: String,
    val confidence: Double,
    val provenance: LayerProvenance,
    val outputCount: Int,
)
