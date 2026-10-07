package dev.axymorrsen.artplusauto

import android.content.pm.ActivityInfo
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.drawable.Drawable

internal object DrawableRenderer {
    fun rawLauncherIcon(pm: PackageManager, info: ActivityInfo): Drawable {
        val resId = info.iconResource
        if (resId != 0) {
            runCatching {
                val resources = pm.getResourcesForApplication(info.applicationInfo)
                @Suppress("DEPRECATION")
                return resources.getDrawable(resId, null)
            }
        }
        return info.loadIcon(pm)
    }

    fun render(drawable: Drawable, width: Int, height: Int, transparent: Boolean = true): Bitmap {
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        canvas.drawColor(if (transparent) Color.TRANSPARENT else Color.WHITE)
        val old = drawable.bounds
        drawable.setBounds(0, 0, width, height)
        drawable.draw(canvas)
        drawable.bounds = old
        return bitmap
    }

    fun resize(source: Bitmap, width: Int, height: Int): Bitmap {
        if (source.width == width && source.height == height) return source
        return Bitmap.createScaledBitmap(source, width, height, true)
    }

    fun centerOnCanvas(source: Bitmap, width: Int, height: Int): Bitmap {
        val out = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        val left = (width - source.width) / 2f
        val top = (height - source.height) / 2f
        canvas.drawBitmap(source, left, top, null)
        return out
    }

    fun alphaCoverage(source: Bitmap, threshold: Int = 12): Double {
        val pixels = IntArray(source.width * source.height)
        source.getPixels(pixels, 0, source.width, 0, 0, source.width, source.height)
        val visible = pixels.count { Color.alpha(it) > threshold }
        return visible.toDouble() / pixels.size.coerceAtLeast(1).toDouble()
    }

    fun touchesEdges(source: Bitmap, threshold: Int = 48): Boolean {
        val w = source.width
        val h = source.height
        if (w == 0 || h == 0) return false
        var touched = 0
        for (x in 0 until w) {
            if (Color.alpha(source.getPixel(x, 0)) > threshold) touched++
            if (Color.alpha(source.getPixel(x, h - 1)) > threshold) touched++
        }
        for (y in 1 until h - 1) {
            if (Color.alpha(source.getPixel(0, y)) > threshold) touched++
            if (Color.alpha(source.getPixel(w - 1, y)) > threshold) touched++
        }
        val perimeter = 2 * w + 2 * h - 4
        return touched > perimeter * 0.08
    }
}
