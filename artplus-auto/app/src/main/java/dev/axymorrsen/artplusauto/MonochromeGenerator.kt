package dev.axymorrsen.artplusauto

import android.graphics.Bitmap
import android.graphics.Color

internal object MonochromeGenerator {
    fun generate(foreground: Bitmap, native: Bitmap?): Bitmap {
        if (native != null) return alphaSilhouette(native)

        val coverage = DrawableRenderer.alphaCoverage(foreground)
        return if (coverage <= 0.76) {
            alphaSilhouette(foreground)
        } else {
            aospStyleFallback(foreground)
        }
    }

    private fun alphaSilhouette(source: Bitmap): Bitmap {
        val w = source.width
        val h = source.height
        val input = IntArray(w * h)
        val out = IntArray(input.size)
        source.getPixels(input, 0, w, 0, 0, w, h)
        for (i in input.indices) {
            val a = Color.alpha(input[i])
            out[i] = if (a == 0) Color.TRANSPARENT else Color.argb(a, 0, 0, 0)
        }
        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
            it.setPixels(out, 0, w, 0, 0, w, h)
        }
    }

    private fun aospStyleFallback(source: Bitmap): Bitmap {
        val w = source.width
        val h = source.height
        val input = IntArray(w * h)
        source.getPixels(input, 0, w, 0, 0, w, h)

        val gray = DoubleArray(input.size)
        var perimeterSum = 0.0
        var perimeterCount = 0
        var totalSum = 0.0
        var visibleCount = 0

        for (i in input.indices) {
            val p = input[i]
            val alpha = Color.alpha(p) / 255.0
            val l = ColorMath.luminance01(p)
            gray[i] = l
            if (alpha > 0.05) {
                totalSum += l
                visibleCount++
            }
            val x = i % w
            val y = i / w
            if ((x <= 2 || y <= 2 || x >= w - 3 || y >= h - 3) && alpha > 0.05) {
                perimeterSum += l
                perimeterCount++
            }
        }

        val overall = if (visibleCount == 0) 0.5 else totalSum / visibleCount
        val perimeter = if (perimeterCount == 0) overall else perimeterSum / perimeterCount
        val invert = perimeter > overall + 0.05

        val tonal = DoubleArray(input.size)
        val visibleTonal = ArrayList<Double>()
        for (i in input.indices) {
            val v = if (invert) 1.0 - gray[i] else gray[i]
            tonal[i] = v
            if (Color.alpha(input[i]) > 12) visibleTonal += v
        }
        val low = ColorMath.percentile(visibleTonal.toDoubleArray(), 0.04)
        val high = ColorMath.percentile(visibleTonal.toDoubleArray(), 0.96).coerceAtLeast(low + 0.04)

        val out = IntArray(input.size)
        for (i in input.indices) {
            val sourceAlpha = Color.alpha(input[i]) / 255.0
            val normalized = ((tonal[i] - low) / (high - low)).coerceIn(0.0, 1.0)
            val alpha = (sourceAlpha * normalized * 255.0 + 0.5).toInt().coerceIn(0, 255)
            out[i] = if (alpha == 0) Color.TRANSPARENT else Color.argb(alpha, 0, 0, 0)
        }

        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
            it.setPixels(out, 0, w, 0, 0, w, h)
        }
    }
}
