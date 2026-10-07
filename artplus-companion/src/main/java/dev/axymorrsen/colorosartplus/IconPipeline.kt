package dev.axymorrsen.colorosartplus

import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.drawable.AdaptiveIconDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.Drawable
import android.os.Build
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import kotlin.math.cbrt
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.roundToInt
import kotlin.math.sqrt

internal object IconPipeline {
    private const val BASE = 240
    private const val W_1X2 = 240
    private const val H_1X2 = 820
    private const val W_2X1 = 820
    private const val H_2X1 = 240
    private const val S_2X2 = 704

    internal data class Target(
        val packageName: String,
        val label: String,
        val icon: Drawable,
    )

    internal data class Output(
        val original: Bitmap,
        val recfg: Bitmap,
        val recbg: Bitmap,
        val night: Bitmap,
        val monochrome: Bitmap,
        val adaptive: Boolean,
        val conservative: Boolean,
    ) {
        fun preview(): Bitmap {
            val out = Bitmap.createBitmap(BASE, BASE, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(out)
            canvas.drawBitmap(recbg, 0f, 0f, null)
            canvas.drawBitmap(night, 0f, 0f, null)
            return out
        }
    }

    suspend fun launcherTargets(pm: PackageManager, selfPackage: String): List<Target> =
        withContext(Dispatchers.Default) {
            val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
            val seen = HashSet<String>()
            pm.queryIntentActivities(intent, 0)
                .asSequence()
                .mapNotNull { ri ->
                    val info = ri.activityInfo ?: return@mapNotNull null
                    val pkg = info.packageName ?: return@mapNotNull null
                    if (pkg == selfPackage || !seen.add(pkg)) return@mapNotNull null
                    val label = runCatching { ri.loadLabel(pm).toString() }.getOrDefault(pkg)
                    val icon = runCatching { ri.loadIcon(pm) }.getOrNull() ?: return@mapNotNull null
                    Target(pkg, label, icon)
                }
                .sortedBy { it.label.lowercase() }
                .toList()
        }

    suspend fun generate(icon: Drawable): Output = withContext(Dispatchers.Default) {
        val original = draw(icon, BASE, BASE)
        if (Build.VERSION.SDK_INT >= 26 && icon is AdaptiveIconDrawable) {
            val bg = draw(icon.background ?: ColorDrawable(Color.TRANSPARENT), BASE, BASE)
            val fg = draw(icon.foreground ?: ColorDrawable(Color.TRANSPARENT), BASE, BASE)
            val nativeMono = if (Build.VERSION.SDK_INT >= 33) {
                icon.monochrome?.let { draw(it, BASE, BASE) }
            } else {
                null
            }
            val night = nightForeground(fg, bg)
            val mono = nativeMono?.let(::normalizeNativeMono) ?: monochrome(fg)
            return@withContext Output(
                original = original,
                recfg = fg,
                recbg = bg,
                night = night,
                monochrome = mono,
                adaptive = true,
                conservative = false,
            )
        }

        val legacy = splitLegacy(original)
        val night = nightForeground(legacy.first, legacy.second)
        Output(
            original = original,
            recfg = legacy.first,
            recbg = legacy.second,
            night = night,
            monochrome = monochrome(legacy.first),
            adaptive = false,
            conservative = legacy.third,
        )
    }

    suspend fun writeAssets(output: Output, dir: File) = withContext(Dispatchers.IO) {
        if (!dir.mkdirs() && !dir.isDirectory) error("无法创建 ${dir.absolutePath}")

        save(output.recbg, File(dir, "recbg.png"))
        save(output.recfg, File(dir, "recfg.png"))
        save(output.night, File(dir, "rec_night.png"))
        save(output.monochrome, File(dir, "monochrome.png"))

        save(scaleFill(output.recbg, W_1X2, H_1X2), File(dir, "recbg_1x2.png"))
        save(scaleFill(output.recbg, W_2X1, H_2X1), File(dir, "recbg_2x1.png"))
        save(scaleFill(output.recbg, S_2X2, S_2X2), File(dir, "recbg_2x2.png"))

        save(center(output.recfg, W_1X2, H_1X2), File(dir, "recfg_1x2.png"))
        save(center(output.recfg, W_2X1, H_2X1), File(dir, "recfg_2x1.png"))
        save(center(output.recfg, S_2X2, S_2X2), File(dir, "recfg_2x2.png"))

        save(center(output.night, W_1X2, H_1X2), File(dir, "rec_night_1x2.png"))
        save(center(output.night, W_2X1, H_2X1), File(dir, "rec_night_2x1.png"))
        save(center(output.night, S_2X2, S_2X2), File(dir, "rec_night_2x2.png"))

        save(center(output.monochrome, W_1X2, H_1X2), File(dir, "monochrome_1x2.png"))
        save(center(output.monochrome, W_2X1, H_2X1), File(dir, "monochrome_2x1.png"))
        save(center(output.monochrome, S_2X2, S_2X2), File(dir, "monochrome_2x2.png"))
    }

    private fun splitLegacy(source: Bitmap): Triple<Bitmap, Bitmap, Boolean> {
        val edge = estimateEdge(source)
        if (edge.opaqueRatio < 0.35 || edge.confidence < 0.68) {
            return Triple(source, transparent(BASE, BASE), true)
        }

        val bg = solid(BASE, BASE, edge.color)
        val fg = subtract(source, edge.color)
        val coverage = alphaCoverage(fg)
        if (coverage < 0.045 || coverage > 0.84 || touchesAllEdges(fg)) {
            return Triple(source, transparent(BASE, BASE), true)
        }
        return Triple(fg, bg, false)
    }

    private data class EdgeModel(
        val color: Int,
        val opaqueRatio: Double,
        val confidence: Double,
    )

    private fun estimateEdge(source: Bitmap): EdgeModel {
        val w = source.width
        val h = source.height
        val band = max(4, (min(w, h) * 0.08f).roundToInt())
        val colors = ArrayList<Int>()
        var total = 0

        for (y in 0 until h) {
            for (x in 0 until w) {
                if (!(x < band || y < band || x >= w - band || y >= h - band)) continue
                total++
                val p = source.getPixel(x, y)
                if (Color.alpha(p) >= 220) colors += p
            }
        }

        if (colors.isEmpty()) return EdgeModel(Color.TRANSPARENT, 0.0, 0.0)
        val rs = colors.map(Color::red).sorted()
        val gs = colors.map(Color::green).sorted()
        val bs = colors.map(Color::blue).sorted()
        val mid = colors.size / 2
        val color = Color.rgb(rs[mid], gs[mid], bs[mid])
        val lab = okLab(color)

        var deviation = 0.0
        var samples = 0
        colors.forEachIndexed { index, p ->
            if (index % 2 == 0) {
                deviation += deltaE(okLab(p), lab)
                samples++
            }
        }

        val opaqueRatio = colors.size.toDouble() / total.coerceAtLeast(1).toDouble()
        val meanDeviation = if (samples == 0) 1.0 else deviation / samples
        val uniformity = clamp01(1.0 - meanDeviation / 0.16)
        val confidence = clamp01(opaqueRatio * 0.55 + uniformity * 0.45)
        return EdgeModel(color, opaqueRatio, confidence)
    }

    private fun subtract(source: Bitmap, bgColor: Int): Bitmap {
        val w = source.width
        val h = source.height
        val src = IntArray(w * h)
        val dst = IntArray(src.size)
        source.getPixels(src, 0, w, 0, 0, w, h)
        val bg = okLab(bgColor)

        for (i in src.indices) {
            val p = src[i]
            val sourceAlpha = Color.alpha(p)
            if (sourceAlpha <= 3) {
                dst[i] = Color.TRANSPARENT
                continue
            }

            val distance = deltaE(okLab(p), bg)
            val mask = smoothStep(0.025, 0.18, distance)
            val alpha = (sourceAlpha * mask).roundToInt().coerceIn(0, 255)
            if (alpha <= 5) {
                dst[i] = Color.TRANSPARENT
                continue
            }

            val a = max(0.02, mask)
            dst[i] = Color.argb(
                alpha,
                unComposite(Color.red(p), Color.red(bgColor), a),
                unComposite(Color.green(p), Color.green(bgColor), a),
                unComposite(Color.blue(p), Color.blue(bgColor), a),
            )
        }

        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
            it.setPixels(dst, 0, w, 0, 0, w, h)
        }
    }

    private fun nightForeground(source: Bitmap, background: Bitmap): Bitmap {
        val w = source.width
        val h = source.height
        val src = IntArray(w * h)
        val dst = IntArray(src.size)
        source.getPixels(src, 0, w, 0, 0, w, h)
        val bgL = meanLightness(background)

        for (i in src.indices) {
            val p = src[i]
            val alpha = Color.alpha(p)
            if (alpha == 0) {
                dst[i] = Color.TRANSPARENT
                continue
            }

            val lab = okLab(p)
            var l = lab[0]
            var a = lab[1]
            var b = lab[2]
            val chroma = hypot(a, b)

            if (bgL < 0.55) {
                l = when {
                    chroma < 0.045 && l < 0.50 -> max(l, 0.78)
                    l < 0.46 -> max(l, 0.62)
                    l < 0.60 -> l + (0.62 - l) * 0.45
                    else -> l
                }
            } else if (l < 0.20 && chroma < 0.035) {
                l = 0.30
            }

            if (chroma > 0.30) {
                val scale = 0.30 / chroma
                a *= scale
                b *= scale
            }
            dst[i] = fromOkLab(alpha, l, a, b)
        }

        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
            it.setPixels(dst, 0, w, 0, 0, w, h)
        }
    }

    private fun normalizeNativeMono(source: Bitmap): Bitmap {
        val w = source.width
        val h = source.height
        val src = IntArray(w * h)
        val dst = IntArray(src.size)
        source.getPixels(src, 0, w, 0, 0, w, h)
        for (i in src.indices) {
            val p = src[i]
            val alpha = Color.alpha(p)
            if (alpha == 0) {
                dst[i] = Color.TRANSPARENT
                continue
            }
            val outAlpha = (alpha * (0.18 + 0.82 * luma(p) / 255.0)).roundToInt().coerceIn(0, 255)
            dst[i] = Color.argb(outAlpha, 255, 255, 255)
        }
        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
            it.setPixels(dst, 0, w, 0, 0, w, h)
        }
    }

    private fun monochrome(source: Bitmap): Bitmap {
        val w = source.width
        val h = source.height
        val src = IntArray(w * h)
        val dst = IntArray(src.size)
        source.getPixels(src, 0, w, 0, 0, w, h)

        var minL = 255
        var maxL = 0
        var visible = 0
        for (p in src) {
            if (Color.alpha(p) <= 8) continue
            val l = luma(p)
            minL = min(minL, l)
            maxL = max(maxL, l)
            visible++
        }

        val flat = visible == 0 || maxL - minL < 28
        for (i in src.indices) {
            val p = src[i]
            val alpha = Color.alpha(p)
            if (alpha == 0) {
                dst[i] = Color.TRANSPARENT
                continue
            }
            val tonal = if (flat) {
                1.0
            } else {
                val n = (luma(p) - minL).toDouble() / (maxL - minL).coerceAtLeast(1).toDouble()
                0.18 + 0.82 * n
            }
            dst[i] = Color.argb((alpha * tonal).roundToInt().coerceIn(0, 255), 255, 255, 255)
        }

        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
            it.setPixels(dst, 0, w, 0, 0, w, h)
        }
    }

    private fun draw(drawable: Drawable, width: Int, height: Int): Bitmap {
        val out = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        val old = drawable.bounds
        drawable.setBounds(0, 0, width, height)
        drawable.draw(canvas)
        drawable.bounds = old
        return out
    }

    private fun save(bitmap: Bitmap, file: File) {
        FileOutputStream(file).use { out ->
            check(bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)) {
                "PNG 编码失败: ${file.name}"
            }
        }
    }

    private fun scaleFill(source: Bitmap, width: Int, height: Int): Bitmap =
        Bitmap.createScaledBitmap(source, width, height, true)

    private fun center(source: Bitmap, width: Int, height: Int): Bitmap {
        val out = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        canvas.drawBitmap(
            source,
            (width - source.width) / 2f,
            (height - source.height) / 2f,
            null,
        )
        return out
    }

    private fun transparent(width: Int, height: Int): Bitmap =
        Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)

    private fun solid(width: Int, height: Int, color: Int): Bitmap =
        Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888).also {
            Canvas(it).drawColor(Color.rgb(Color.red(color), Color.green(color), Color.blue(color)))
        }

    private fun alphaCoverage(source: Bitmap): Double {
        val pixels = IntArray(source.width * source.height)
        source.getPixels(pixels, 0, source.width, 0, 0, source.width, source.height)
        return pixels.count { Color.alpha(it) > 20 }.toDouble() / pixels.size.coerceAtLeast(1)
    }

    private fun touchesAllEdges(source: Bitmap): Boolean {
        var top = false
        var bottom = false
        var left = false
        var right = false
        for (x in 0 until source.width) {
            top = top || Color.alpha(source.getPixel(x, 0)) > 20
            bottom = bottom || Color.alpha(source.getPixel(x, source.height - 1)) > 20
        }
        for (y in 0 until source.height) {
            left = left || Color.alpha(source.getPixel(0, y)) > 20
            right = right || Color.alpha(source.getPixel(source.width - 1, y)) > 20
        }
        return top && bottom && left && right
    }

    private fun unComposite(visible: Int, background: Int, alpha: Double): Int =
        ((visible - (1.0 - alpha) * background) / alpha).roundToInt().coerceIn(0, 255)

    private fun luma(color: Int): Int =
        (0.2126 * Color.red(color) + 0.7152 * Color.green(color) + 0.0722 * Color.blue(color))
            .roundToInt()
            .coerceIn(0, 255)

    private fun meanLightness(bitmap: Bitmap): Double {
        val pixels = IntArray(bitmap.width * bitmap.height)
        bitmap.getPixels(pixels, 0, bitmap.width, 0, 0, bitmap.width, bitmap.height)
        var weighted = 0.0
        var weight = 0.0
        for (p in pixels) {
            val alpha = Color.alpha(p)
            if (alpha <= 8) continue
            val w = alpha / 255.0
            weighted += okLab(p)[0] * w
            weight += w
        }
        return if (weight > 0.0) weighted / weight else 0.25
    }

    private fun smoothStep(a: Double, b: Double, x: Double): Double {
        val t = clamp01((x - a) / (b - a))
        return t * t * (3.0 - 2.0 * t)
    }

    private fun deltaE(a: DoubleArray, b: DoubleArray): Double {
        val dl = a[0] - b[0]
        val da = a[1] - b[1]
        val db = a[2] - b[2]
        return sqrt(dl * dl + da * da + db * db)
    }

    private fun okLab(color: Int): DoubleArray {
        val r = srgbToLinear(Color.red(color) / 255.0)
        val g = srgbToLinear(Color.green(color) / 255.0)
        val b = srgbToLinear(Color.blue(color) / 255.0)

        val l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
        val m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
        val s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

        val lp = cbrt(l)
        val mp = cbrt(m)
        val sp = cbrt(s)

        return doubleArrayOf(
            0.2104542553 * lp + 0.7936177850 * mp - 0.0040720468 * sp,
            1.9779984951 * lp - 2.4285922050 * mp + 0.4505937099 * sp,
            0.0259040371 * lp + 0.7827717662 * mp - 0.8086757660 * sp,
        )
    }

    private fun fromOkLab(alpha: Int, lValue: Double, aValue: Double, bValue: Double): Int {
        val lp = lValue + 0.3963377774 * aValue + 0.2158037573 * bValue
        val mp = lValue - 0.1055613458 * aValue - 0.0638541728 * bValue
        val sp = lValue - 0.0894841775 * aValue - 1.2914855480 * bValue

        val l = lp * lp * lp
        val m = mp * mp * mp
        val s = sp * sp * sp

        val r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
        val g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
        val b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

        return Color.argb(
            alpha.coerceIn(0, 255),
            (linearToSrgb(r) * 255.0).roundToInt().coerceIn(0, 255),
            (linearToSrgb(g) * 255.0).roundToInt().coerceIn(0, 255),
            (linearToSrgb(b) * 255.0).roundToInt().coerceIn(0, 255),
        )
    }

    private fun srgbToLinear(value: Double): Double {
        val v = clamp01(value)
        return if (v <= 0.04045) v / 12.92 else ((v + 0.055) / 1.055).pow(2.4)
    }

    private fun linearToSrgb(value: Double): Double {
        val v = clamp01(value)
        return if (v <= 0.0031308) v * 12.92 else 1.055 * v.pow(1.0 / 2.4) - 0.055
    }

    private fun clamp01(value: Double): Double = value.coerceIn(0.0, 1.0)
}
