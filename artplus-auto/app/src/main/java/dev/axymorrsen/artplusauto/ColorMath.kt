package dev.axymorrsen.artplusauto

import android.graphics.Color
import kotlin.math.cbrt
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.sqrt

internal data class OkLab(val l: Double, val a: Double, val b: Double) {
    val chroma: Double get() = sqrt(a * a + b * b)
}

internal object ColorMath {
    fun toLab(color: Int): OkLab {
        val r = srgbToLinear(Color.red(color) / 255.0)
        val g = srgbToLinear(Color.green(color) / 255.0)
        val b = srgbToLinear(Color.blue(color) / 255.0)

        val l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
        val m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
        val s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

        val ll = cbrt(l)
        val mm = cbrt(m)
        val ss = cbrt(s)

        return OkLab(
            0.2104542553 * ll + 0.7936177850 * mm - 0.0040720468 * ss,
            1.9779984951 * ll - 2.4285922050 * mm + 0.4505937099 * ss,
            0.0259040371 * ll + 0.7827717662 * mm - 0.8086757660 * ss,
        )
    }

    fun fromLab(alpha: Int, lab: OkLab): Int {
        val ll = lab.l + 0.3963377774 * lab.a + 0.2158037573 * lab.b
        val mm = lab.l - 0.1055613458 * lab.a - 0.0638541728 * lab.b
        val ss = lab.l - 0.0894841775 * lab.a - 1.2914855480 * lab.b

        val l = ll * ll * ll
        val m = mm * mm * mm
        val s = ss * ss * ss

        val r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
        val g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
        val b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

        return Color.argb(
            alpha.coerceIn(0, 255),
            (linearToSrgb(r).coerceIn(0.0, 1.0) * 255.0 + 0.5).toInt(),
            (linearToSrgb(g).coerceIn(0.0, 1.0) * 255.0 + 0.5).toInt(),
            (linearToSrgb(b).coerceIn(0.0, 1.0) * 255.0 + 0.5).toInt(),
        )
    }

    fun distance(a: Int, b: Int): Double {
        val x = toLab(a)
        val y = toLab(b)
        val dl = x.l - y.l
        val da = x.a - y.a
        val db = x.b - y.b
        return sqrt(dl * dl + da * da + db * db)
    }

    fun luminance01(color: Int): Double = toLab(color).l.coerceIn(0.0, 1.0)

    fun smoothstep(edge0: Double, edge1: Double, x: Double): Double {
        if (edge1 <= edge0) return if (x >= edge1) 1.0 else 0.0
        val t = ((x - edge0) / (edge1 - edge0)).coerceIn(0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)
    }

    fun percentile(values: DoubleArray, p: Double): Double {
        if (values.isEmpty()) return 0.0
        val copy = values.copyOf()
        copy.sort()
        val index = ((copy.size - 1) * p.coerceIn(0.0, 1.0)).toInt()
        return copy[index]
    }

    fun medianColor(colors: IntArray): Int {
        if (colors.isEmpty()) return Color.TRANSPARENT
        val rs = IntArray(colors.size)
        val gs = IntArray(colors.size)
        val bs = IntArray(colors.size)
        for (i in colors.indices) {
            rs[i] = Color.red(colors[i])
            gs[i] = Color.green(colors[i])
            bs[i] = Color.blue(colors[i])
        }
        rs.sort(); gs.sort(); bs.sort()
        val mid = colors.size / 2
        return Color.rgb(rs[mid], gs[mid], bs[mid])
    }

    private fun srgbToLinear(v: Double): Double =
        if (v <= 0.04045) v / 12.92 else ((v + 0.055) / 1.055).pow(2.4)

    private fun linearToSrgb(v: Double): Double =
        if (v <= 0.0031308) 12.92 * v else 1.055 * max(v, 0.0).pow(1.0 / 2.4) - 0.055
}
