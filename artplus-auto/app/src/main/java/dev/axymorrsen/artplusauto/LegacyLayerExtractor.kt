package dev.axymorrsen.artplusauto

import android.graphics.Bitmap
import android.graphics.Color
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

internal object LegacyLayerExtractor {
    private const val LOW_DISTANCE = 0.022
    private const val HIGH_DISTANCE = 0.145
    private const val CONSERVATIVE_THRESHOLD = 0.65

    fun extract(sourceInput: Bitmap): IconLayers {
        val source = DrawableRenderer.resize(
            sourceInput,
            ArtPlusSpec.SIZE_1X1,
            ArtPlusSpec.SIZE_1X1,
        )
        val w = source.width
        val h = source.height
        val sourcePixels = IntArray(w * h)
        source.getPixels(sourcePixels, 0, w, 0, 0, w, h)

        val visibleCoverage = sourcePixels.count { Color.alpha(it) > 16 }.toDouble() / sourcePixels.size
        val perimeterTransparent = perimeterTransparentRatio(source)
        if (perimeterTransparent > 0.28 && visibleCoverage < 0.82) {
            return IconLayers(
                foreground = source,
                background = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888),
                nativeMonochrome = null,
                confidence = 0.88,
                provenance = LayerProvenance.LEGACY_CONSERVATIVE,
            )
        }

        val model = BackgroundModel.from(source)
        val background = model.render(w, h)
        val bgPixels = IntArray(w * h)
        background.getPixels(bgPixels, 0, w, 0, 0, w, h)

        val out = IntArray(sourcePixels.size)
        var subjectPixels = 0
        var edgeSubjectPixels = 0
        for (i in sourcePixels.indices) {
            val src = sourcePixels[i]
            val srcAlpha = Color.alpha(src) / 255.0
            if (srcAlpha <= 0.001) {
                out[i] = Color.TRANSPARENT
                continue
            }
            val distance = ColorMath.distance(src, bgPixels[i])
            val separation = ColorMath.smoothstep(LOW_DISTANCE, HIGH_DISTANCE, distance)
            val alpha = (srcAlpha * separation).coerceIn(0.0, 1.0)
            if (alpha <= 0.015) {
                out[i] = Color.TRANSPARENT
                continue
            }
            subjectPixels++
            val x = i % w
            val y = i / w
            if (x <= 1 || y <= 1 || x >= w - 2 || y >= h - 2) edgeSubjectPixels++
            out[i] = inverseComposite(src, bgPixels[i], alpha)
        }

        val foreground = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        foreground.setPixels(out, 0, w, 0, 0, w, h)

        val subjectCoverage = subjectPixels.toDouble() / sourcePixels.size
        val edgeTouchRatio = if (subjectPixels == 0) 1.0 else edgeSubjectPixels.toDouble() / subjectPixels
        var confidence = 1.0 - (model.perimeterP90 / 0.16).coerceIn(0.0, 1.0) * 0.58
        if (subjectCoverage !in 0.025..0.74) confidence -= 0.22
        if (edgeTouchRatio > 0.06) confidence -= 0.22
        confidence = confidence.coerceIn(0.0, 1.0)

        return if (confidence >= CONSERVATIVE_THRESHOLD) {
            IconLayers(
                foreground = foreground,
                background = background,
                nativeMonochrome = null,
                confidence = confidence,
                provenance = LayerProvenance.LEGACY_SEPARATED,
            )
        } else {
            IconLayers(
                foreground = source,
                background = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888),
                nativeMonochrome = null,
                confidence = confidence,
                provenance = LayerProvenance.LEGACY_CONSERVATIVE,
            )
        }
    }

    fun subtractKnownBackground(composedInput: Bitmap, backgroundInput: Bitmap): Bitmap {
        val composed = DrawableRenderer.resize(composedInput, ArtPlusSpec.SIZE_1X1, ArtPlusSpec.SIZE_1X1)
        val background = DrawableRenderer.resize(backgroundInput, ArtPlusSpec.SIZE_1X1, ArtPlusSpec.SIZE_1X1)
        val w = composed.width
        val h = composed.height
        val cp = IntArray(w * h)
        val bp = IntArray(w * h)
        val out = IntArray(w * h)
        composed.getPixels(cp, 0, w, 0, 0, w, h)
        background.getPixels(bp, 0, w, 0, 0, w, h)

        for (i in cp.indices) {
            val sourceAlpha = Color.alpha(cp[i]) / 255.0
            if (sourceAlpha <= 0.001) {
                out[i] = Color.TRANSPARENT
                continue
            }
            val d = ColorMath.distance(cp[i], bp[i])
            val separated = ColorMath.smoothstep(0.018, 0.125, d)
            val alpha = (sourceAlpha * separated).coerceIn(0.0, 1.0)
            out[i] = if (alpha <= 0.012) Color.TRANSPARENT else inverseComposite(cp[i], bp[i], alpha)
        }
        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
            it.setPixels(out, 0, w, 0, 0, w, h)
        }
    }

    private fun inverseComposite(visible: Int, background: Int, alpha: Double): Int {
        val a = alpha.coerceIn(0.02, 1.0)
        fun restore(v: Int, b: Int): Int =
            ((v - (1.0 - a) * b) / a).toInt().coerceIn(0, 255)
        return Color.argb(
            (alpha * 255.0 + 0.5).toInt().coerceIn(0, 255),
            restore(Color.red(visible), Color.red(background)),
            restore(Color.green(visible), Color.green(background)),
            restore(Color.blue(visible), Color.blue(background)),
        )
    }

    private fun perimeterTransparentRatio(source: Bitmap): Double {
        val w = source.width
        val h = source.height
        var total = 0
        var transparent = 0
        fun sample(x: Int, y: Int) {
            total++
            if (Color.alpha(source.getPixel(x, y)) < 64) transparent++
        }
        for (x in 0 until w) {
            sample(x, 0); sample(x, h - 1)
        }
        for (y in 1 until h - 1) {
            sample(0, y); sample(w - 1, y)
        }
        return transparent.toDouble() / total.coerceAtLeast(1)
    }

    private data class BackgroundModel(
        val tl: Int,
        val tr: Int,
        val bl: Int,
        val br: Int,
        val perimeterP90: Double,
    ) {
        fun render(width: Int, height: Int): Bitmap {
            val pixels = IntArray(width * height)
            for (y in 0 until height) {
                val fy = if (height <= 1) 0.0 else y.toDouble() / (height - 1)
                for (x in 0 until width) {
                    val fx = if (width <= 1) 0.0 else x.toDouble() / (width - 1)
                    val top = lerp(tl, tr, fx)
                    val bottom = lerp(bl, br, fx)
                    pixels[y * width + x] = lerp(top, bottom, fy)
                }
            }
            return Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888).also {
                it.setPixels(pixels, 0, width, 0, 0, width, height)
            }
        }

        private fun lerp(a: Int, b: Int, t: Double): Int =
            Color.rgb(
                (Color.red(a) + (Color.red(b) - Color.red(a)) * t).toInt().coerceIn(0, 255),
                (Color.green(a) + (Color.green(b) - Color.green(a)) * t).toInt().coerceIn(0, 255),
                (Color.blue(a) + (Color.blue(b) - Color.blue(a)) * t).toInt().coerceIn(0, 255),
            )

        companion object {
            fun from(source: Bitmap): BackgroundModel {
                val patch = max(6, min(source.width, source.height) / 10)
                val tl = medianPatch(source, 0, 0, patch, patch)
                val tr = medianPatch(source, source.width - patch, 0, source.width, patch)
                val bl = medianPatch(source, 0, source.height - patch, patch, source.height)
                val br = medianPatch(source, source.width - patch, source.height - patch, source.width, source.height)

                val provisional = BackgroundModel(tl, tr, bl, br, 0.0)
                val rendered = provisional.render(source.width, source.height)
                val residuals = ArrayList<Double>()
                val band = max(2, min(source.width, source.height) / 20)
                for (y in 0 until source.height) {
                    for (x in 0 until source.width) {
                        if (x >= band && x < source.width - band && y >= band && y < source.height - band) continue
                        val p = source.getPixel(x, y)
                        if (Color.alpha(p) < 160) continue
                        residuals += ColorMath.distance(p, rendered.getPixel(x, y))
                    }
                }
                return provisional.copy(
                    perimeterP90 = ColorMath.percentile(residuals.toDoubleArray(), 0.90),
                )
            }

            private fun medianPatch(source: Bitmap, left: Int, top: Int, right: Int, bottom: Int): Int {
                val colors = ArrayList<Int>()
                for (y in top.coerceAtLeast(0) until bottom.coerceAtMost(source.height)) {
                    for (x in left.coerceAtLeast(0) until right.coerceAtMost(source.width)) {
                        val p = source.getPixel(x, y)
                        if (Color.alpha(p) >= 160) colors += p
                    }
                }
                if (colors.isEmpty()) return Color.TRANSPARENT
                return ColorMath.medianColor(colors.toIntArray())
            }
        }
    }
}
