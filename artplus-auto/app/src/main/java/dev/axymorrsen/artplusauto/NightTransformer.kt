package dev.axymorrsen.artplusauto

import android.graphics.Bitmap
import android.graphics.Color
import kotlin.math.max
import kotlin.math.min

internal object NightTransformer {
    fun transform(foreground: Bitmap, background: Bitmap): Bitmap {
        val w = foreground.width
        val h = foreground.height
        val source = IntArray(w * h)
        foreground.getPixels(source, 0, w, 0, 0, w, h)
        val bgL = backgroundLightness(background)

        val out = IntArray(source.size)
        for (i in source.indices) {
            val p = source[i]
            val alpha = Color.alpha(p)
            if (alpha == 0) {
                out[i] = Color.TRANSPARENT
                continue
            }
            val lab = ColorMath.toLab(p)
            val c = lab.chroma
            var targetL = lab.l
            var chromaScale = 1.0

            if (c < 0.035) {
                targetL = when {
                    lab.l < 0.22 -> 0.72
                    lab.l < 0.38 -> 0.68 + lab.l * 0.10
                    lab.l < 0.56 -> max(lab.l, 0.63)
                    lab.l > 0.93 -> 0.93
                    else -> lab.l
                }
            } else {
                when {
                    lab.l < 0.20 -> {
                        targetL = 0.54 + lab.l * 0.35
                        chromaScale = 0.90
                    }
                    lab.l < 0.38 -> {
                        targetL = lab.l + (0.56 - lab.l) * 0.62
                        chromaScale = 0.94
                    }
                    lab.l < 0.48 -> {
                        targetL = lab.l + (0.53 - lab.l) * 0.32
                        chromaScale = 0.97
                    }
                }
            }

            if (bgL < 0.34 && c < 0.045 && targetL - bgL < 0.42) {
                targetL = max(targetL, 0.72)
            }

            val target = OkLab(
                l = targetL.coerceIn(0.0, 0.95),
                a = lab.a * chromaScale,
                b = lab.b * chromaScale,
            )
            out[i] = ColorMath.fromLab(alpha, target)
        }

        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
            it.setPixels(out, 0, w, 0, 0, w, h)
        }
    }

    private fun backgroundLightness(background: Bitmap): Double {
        val samples = ArrayList<Double>()
        val w = background.width
        val h = background.height
        val points = arrayOf(
            0 to 0,
            (w - 1) to 0,
            0 to (h - 1),
            (w - 1) to (h - 1),
            (w / 2) to (h / 2),
        )
        for ((x, y) in points) {
            val p = background.getPixel(x.coerceIn(0, w - 1), y.coerceIn(0, h - 1))
            if (Color.alpha(p) > 24) samples += ColorMath.luminance01(p)
        }
        if (samples.isEmpty()) return 0.16
        samples.sort()
        return samples[samples.size / 2]
    }
}
