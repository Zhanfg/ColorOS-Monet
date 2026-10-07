package dev.axymorrsen.artplusauto

import android.content.Context
import android.content.pm.ActivityInfo
import android.graphics.Bitmap
import java.io.File

internal class ArtPlusCompiler(
    private val context: Context,
    private val root: RootBridge,
) {
    fun compileAndInstall(activityInfo: ActivityInfo): CompileResult {
        val packageName = activityInfo.packageName
        val pm = context.packageManager
        val icon = DrawableRenderer.rawLauncherIcon(pm, activityInfo)
        val layers = LayerExtractor.extract(icon)
        val night = NightTransformer.transform(layers.foreground, layers.background)
        val mono = MonochromeGenerator.generate(layers.foreground, layers.nativeMonochrome)

        val output = File(context.cacheDir, "artplus-generated/$packageName")
        if (output.exists()) output.deleteRecursively()
        check(output.mkdirs()) { "cannot create staging directory" }

        val files = linkedMapOf<String, Bitmap>()
        files["recfg.png"] = layers.foreground
        files["recbg.png"] = layers.background
        files["rec_night.png"] = night
        files["monochrome.png"] = mono
        files["monochrome_light.png"] = mono
        files["monochrome_dark.png"] = mono

        val spans = listOf(
            Triple("1x2", ArtPlusSpec.SIZE_1X2_W, ArtPlusSpec.SIZE_1X2_H),
            Triple("2x1", ArtPlusSpec.SIZE_2X1_W, ArtPlusSpec.SIZE_2X1_H),
            Triple("2x2", ArtPlusSpec.SIZE_2X2, ArtPlusSpec.SIZE_2X2),
        )
        for ((suffix, width, height) in spans) {
            files["recfg_$suffix.png"] = DrawableRenderer.centerOnCanvas(layers.foreground, width, height)
            files["rec_night_$suffix.png"] = DrawableRenderer.centerOnCanvas(night, width, height)
            files["monochrome_$suffix.png"] = DrawableRenderer.centerOnCanvas(mono, width, height)
            files["recbg_$suffix.png"] = DrawableRenderer.resize(layers.background, width, height)
        }

        for ((name, bitmap) in files) {
            File(output, name).outputStream().use { stream ->
                check(bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream)) {
                    "failed to encode $name"
                }
            }
        }

        root.install(packageName, output)
        return CompileResult(
            packageName = packageName,
            confidence = layers.confidence,
            provenance = layers.provenance,
            outputCount = files.size,
        )
    }
}
