package dev.axymorrsen.artplusauto

import android.graphics.Bitmap
import android.graphics.drawable.AdaptiveIconDrawable
import android.graphics.drawable.Drawable
import android.os.Build

internal object LayerExtractor {
    fun extract(icon: Drawable): IconLayers {
        if (icon !is AdaptiveIconDrawable) {
            val source = DrawableRenderer.render(
                icon,
                ArtPlusSpec.SIZE_1X1 * ArtPlusSpec.RENDER_SCALE,
                ArtPlusSpec.SIZE_1X1 * ArtPlusSpec.RENDER_SCALE,
                transparent = true,
            )
            return LegacyLayerExtractor.extract(source)
        }

        val renderSize = ArtPlusSpec.SIZE_1X1 * ArtPlusSpec.RENDER_SCALE
        val backgroundLarge = DrawableRenderer.render(icon.background, renderSize, renderSize, transparent = true)
        val foregroundLarge = DrawableRenderer.render(icon.foreground, renderSize, renderSize, transparent = true)
        val composedLarge = DrawableRenderer.render(icon, renderSize, renderSize, transparent = true)

        val background = DrawableRenderer.resize(backgroundLarge, ArtPlusSpec.SIZE_1X1, ArtPlusSpec.SIZE_1X1)
        val directForeground = DrawableRenderer.resize(foregroundLarge, ArtPlusSpec.SIZE_1X1, ArtPlusSpec.SIZE_1X1)
        val composed = DrawableRenderer.resize(composedLarge, ArtPlusSpec.SIZE_1X1, ArtPlusSpec.SIZE_1X1)

        val directCoverage = DrawableRenderer.alphaCoverage(directForeground)
        val directUsable =
            directCoverage in 0.02..0.70 &&
                !DrawableRenderer.touchesEdges(directForeground)

        val foreground = if (directUsable) {
            directForeground
        } else {
            LegacyLayerExtractor.subtractKnownBackground(composed, background)
        }

        val mono = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            icon.monochrome?.let { drawable ->
                DrawableRenderer.resize(
                    DrawableRenderer.render(drawable, renderSize, renderSize, transparent = true),
                    ArtPlusSpec.SIZE_1X1,
                    ArtPlusSpec.SIZE_1X1,
                )
            }?.takeIf {
                DrawableRenderer.alphaCoverage(it) in 0.004..0.86
            }
        } else {
            null
        }

        return IconLayers(
            foreground = foreground,
            background = background,
            nativeMonochrome = mono,
            confidence = if (directUsable) 1.0 else 0.93,
            provenance = if (directUsable) {
                LayerProvenance.ADAPTIVE_NATIVE
            } else {
                LayerProvenance.ADAPTIVE_RECOVERED
            },
        )
    }
}
