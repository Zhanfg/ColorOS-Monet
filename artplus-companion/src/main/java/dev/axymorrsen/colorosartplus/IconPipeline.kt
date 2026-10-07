package dev.axymorrsen.colorosartplus

import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Rect
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
        val strategy: GenerationStrategy,
        val flipped: Boolean,
        val confidence: Float,
    ) {
        fun preview(): Bitmap {
            val out = Bitmap.createBitmap(BASE, BASE, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(out)
            val paint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG)
            paint.color = Color.rgb(28, 27, 31)

            // rec_night is the dark-mode foreground asset. Preview it against the
            // launcher-like dark host surface; do not composite the daylight recbg.
            val radius = BASE * 0.22f
            canvas.drawRoundRect(
                0f,
                0f,
                BASE.toFloat(),
                BASE.toFloat(),
                radius,
                radius,
                paint,
            )
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

    suspend fun launcherTargetForPackage(
        pm: PackageManager,
        packageName: String,
    ): Target? = withContext(Dispatchers.Default) {
        val launchIntent = pm.getLaunchIntentForPackage(packageName) ?: return@withContext null
        val resolved = pm.resolveActivity(launchIntent, 0) ?: return@withContext null
        val label = runCatching { resolved.loadLabel(pm).toString() }.getOrDefault(packageName)
        val icon = runCatching { resolved.loadIcon(pm) }.getOrNull() ?: return@withContext null
        Target(packageName, label, icon)
    }

    suspend fun generate(
        icon: Drawable,
        invertOverride: Boolean? = null,
    ): Output = withContext(Dispatchers.Default) {
        val safeIcon = runCatching {
            icon.constantState?.newDrawable()?.mutate() ?: icon.mutate()
        }.getOrDefault(icon)

        val original = draw(safeIcon, BASE, BASE)
        if (Build.VERSION.SDK_INT >= 26 && safeIcon is AdaptiveIconDrawable) {
            val bg = draw(safeIcon.background ?: ColorDrawable(Color.TRANSPARENT), BASE, BASE)
            val fg = draw(safeIcon.foreground ?: ColorDrawable(Color.TRANSPARENT), BASE, BASE)
            val nativeMono = if (Build.VERSION.SDK_INT >= 33) {
                safeIcon.monochrome?.let { draw(it, BASE, BASE) }
            } else {
                null
            }

            val mono = nativeMono?.let {
                MonoResult(
                    bitmap = normalizeNativeMono(it),
                    flipped = false,
                    confidence = 1f,
                )
            } ?: aospMonochrome(fg)

            val night = nightForeground(
                source = fg,
                background = bg,
                adaptive = true,
                invertOverride = invertOverride,
            )

            return@withContext Output(
                original = original,
                recfg = fg,
                recbg = bg,
                night = night.bitmap,
                monochrome = mono.bitmap,
                adaptive = true,
                conservative = false,
                strategy = when {
                    night.inverted -> GenerationStrategy.DarkDominantInvert
                    nativeMono != null -> GenerationStrategy.NativeMonochrome
                    else -> GenerationStrategy.AospMonochrome
                },
                flipped = night.inverted,
                confidence = minOf(mono.confidence, night.confidence),
            )
        }

        val legacy = splitLegacy(original)
        val mono = aospMonochrome(legacy.foreground)
        val night = nightForeground(
            source = legacy.foreground,
            background = legacy.background,
            adaptive = false,
            invertOverride = invertOverride,
        )

        Output(
            original = original,
            recfg = legacy.foreground,
            recbg = legacy.background,
            night = night.bitmap,
            monochrome = mono.bitmap,
            adaptive = false,
            conservative = legacy.conservative,
            strategy = when {
                legacy.conservative -> GenerationStrategy.ConservativeFallback
                night.inverted -> GenerationStrategy.DarkDominantInvert
                else -> GenerationStrategy.LegacyToneLift
            },
            flipped = night.inverted,
            confidence = minOf(legacy.confidence, mono.confidence, night.confidence),
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

    private data class LegacySplit(
        val foreground: Bitmap,
        val background: Bitmap,
        val conservative: Boolean,
        val confidence: Float,
    )

    private fun splitLegacy(source: Bitmap): LegacySplit {
        val edge = estimateEdge(source)
        if (edge.opaqueRatio < 0.35 || edge.confidence < 0.68) {
            return LegacySplit(
                foreground = source,
                background = transparent(BASE, BASE),
                conservative = true,
                confidence = edge.confidence.toFloat().coerceIn(0.25f, 0.58f),
            )
        }

        val bg = solid(BASE, BASE, edge.color)
        val fg = subtract(source, edge.color)
        val coverage = alphaCoverage(fg)
        if (coverage < 0.045 || coverage > 0.84 || touchesAllEdges(fg)) {
            return LegacySplit(
                foreground = source,
                background = transparent(BASE, BASE),
                conservative = true,
                confidence = 0.52f,
            )
        }

        val coverageScore = when {
            coverage in 0.10..0.70 -> 1.0
            coverage in 0.06..0.80 -> 0.82
            else -> 0.68
        }

        return LegacySplit(
            foreground = fg,
            background = bg,
            conservative = false,
            confidence = (edge.confidence * coverageScore).toFloat().coerceIn(0.55f, 0.98f),
        )
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

    private data class NightResult(
        val bitmap: Bitmap,
        val inverted: Boolean,
        val confidence: Float,
    )

    private fun nightForeground(
        source: Bitmap,
        background: Bitmap,
        adaptive: Boolean,
        invertOverride: Boolean?,
    ): NightResult {
        val w = source.width
        val h = source.height
        val src = IntArray(w * h)
        val dst = IntArray(src.size)
        source.getPixels(src, 0, w, 0, 0, w, h)

        var visibleWeight = 0.0
        var darkNeutralWeight = 0.0
        var coloredWeight = 0.0
        var brightWeight = 0.0
        var weightedL = 0.0

        for (p in src) {
            val alpha = Color.alpha(p)
            if (alpha <= 24) continue

            val lab = okLab(p)
            val l = lab[0]
            val chroma = hypot(lab[1], lab[2])
            val weight = alpha / 255.0

            visibleWeight += weight
            weightedL += l * weight

            if (l < 0.44 && chroma < 0.065) {
                darkNeutralWeight += weight
            }
            if (chroma >= 0.075 && l > 0.18) {
                coloredWeight += weight
            }
            if (l > 0.72) {
                brightWeight += weight
            }
        }

        val meanL = if (visibleWeight > 0.0) weightedL / visibleWeight else 0.5
        val darkNeutralRatio =
            if (visibleWeight > 0.0) darkNeutralWeight / visibleWeight else 0.0
        val coloredRatio =
            if (visibleWeight > 0.0) coloredWeight / visibleWeight else 0.0
        val brightRatio =
            if (visibleWeight > 0.0) brightWeight / visibleWeight else 0.0
        val bgL = meanLightness(background)

        // Only genuinely black/gray dominant subjects should invert. Saturated brand
        // marks (Yandex, Google, Telegram, etc.) are protected even when they contain
        // dark antialias/shadow pixels.
        val autoInvert = visibleWeight > 0.0 &&
            meanL < 0.50 &&
            darkNeutralRatio >= 0.48 &&
            coloredRatio <= 0.22 &&
            brightRatio < 0.30
        val invert = invertOverride ?: autoInvert

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

            if (invert) {
                // Selective L* inversion. Very dark detail becomes light while hue is
                // retained; this is intended for genuinely black/gray dominant marks.
                l = when {
                    l < 0.18 -> 0.90 - l * 0.20
                    l < 0.46 -> 0.84 - l * 0.30
                    l < 0.62 -> max(l, 0.66)
                    else -> l
                }
            } else if (bgL < 0.55) {
                // Preserve saturated brand colors. Only neutral/near-neutral dark detail
                // gets the strong night lift. Colored dark pixels receive a small floor
                // so they stay readable without turning pastel.
                l = when {
                    chroma < 0.045 && l < 0.50 -> max(l, 0.80)
                    chroma < 0.075 && l < 0.46 -> max(l, 0.66)
                    chroma >= 0.075 && l < 0.30 -> max(l, 0.42)
                    else -> l
                }
            } else if (l < 0.20 && chroma < 0.035) {
                l = 0.30
            }

            // Only constrain pathological gamut excursions. Ordinary saturated brand
            // colors are intentionally preserved.
            val adjustedChroma = hypot(a, b)
            if (adjustedChroma > 0.36) {
                val scale = 0.36 / adjustedChroma
                a *= scale
                b *= scale
            }

            dst[i] = fromOkLab(alpha, l, a, b)
        }

        val confidence = when {
            visibleWeight <= 0.0 -> 0.35f
            invert && darkNeutralRatio > 0.72 -> 0.95f
            invert -> 0.88f
            coloredRatio > 0.45 -> 0.96f
            adaptive -> 0.94f
            else -> 0.84f
        }

        return NightResult(
            bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
                it.setPixels(dst, 0, w, 0, 0, w, h)
            },
            inverted = invert,
            confidence = confidence,
        )
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

    private data class MonoResult(
        val bitmap: Bitmap,
        val flipped: Boolean,
        val confidence: Float,
    )

    /**
     * AOSP Launcher3 MonochromeIconFactory-style fallback.
     *
     * The original AOSP implementation converts the flattened icon to grayscale/alpha,
     * stretches the min/max range and decides whether to invert from edge brightness.
     * This implementation keeps that behavior while respecting source alpha.
     */
    private fun aospMonochrome(source: Bitmap): MonoResult {
        val w = source.width
        val h = source.height
        val src = IntArray(w * h)
        val intensity = IntArray(src.size)
        val dst = IntArray(src.size)
        source.getPixels(src, 0, w, 0, 0, w, h)

        var minValue = 255
        var maxValue = 0
        var visible = 0

        for (i in src.indices) {
            val p = src[i]
            val alpha = Color.alpha(p)
            val gray = ((Color.red(p) + Color.green(p) + Color.blue(p)) / 3.0)
                .roundToInt()
                .coerceIn(0, 255)
            val value = (gray * (alpha / 255.0)).roundToInt().coerceIn(0, 255)
            intensity[i] = value

            if (alpha > 4) {
                visible++
                minValue = min(minValue, value)
                maxValue = max(maxValue, value)
            }
        }

        if (visible == 0) {
            return MonoResult(
                bitmap = transparent(w, h),
                flipped = false,
                confidence = 0.25f,
            )
        }

        val range = (maxValue - minValue).coerceAtLeast(1)
        val band = max(1, (min(w, h) * 0.08f).roundToInt())
        var edgeSum = 0L
        var edgeCount = 0

        for (y in 0 until h) {
            for (x in 0 until w) {
                if (x >= band && y >= band && x < w - band && y < h - band) continue
                val v = intensity[y * w + x]
                edgeSum += v
                edgeCount++
            }
        }

        val edgeAverage = if (edgeCount > 0) edgeSum.toDouble() / edgeCount else 0.0
        val edgeMapped = ((edgeAverage - minValue) / range.toDouble()).coerceIn(0.0, 1.0)
        val flip = edgeMapped > 0.5

        for (i in src.indices) {
            val p = src[i]
            val alpha = Color.alpha(p)
            if (alpha == 0) {
                dst[i] = Color.TRANSPARENT
                continue
            }

            val normalized = if (maxValue > minValue) {
                ((intensity[i] - minValue) * 255.0 / range)
                    .roundToInt()
                    .coerceIn(0, 255)
            } else {
                alpha
            }

            val mono = if (flip) 255 - normalized else normalized
            val outAlpha = min(alpha, mono).coerceIn(0, 255)
            dst[i] = Color.argb(outAlpha, 255, 255, 255)
        }

        val contrast = (maxValue - minValue) / 255f
        val confidence = (0.58f + contrast * 0.36f).coerceIn(0.58f, 0.96f)

        return MonoResult(
            bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also {
                it.setPixels(dst, 0, w, 0, 0, w, h)
            },
            flipped = flip,
            confidence = confidence,
        )
    }

    private fun draw(drawable: Drawable, width: Int, height: Int): Bitmap {
        val out = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        val old = Rect(drawable.bounds)
        drawable.setBounds(0, 0, width, height)
        drawable.draw(canvas)
        drawable.setBounds(old)
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
