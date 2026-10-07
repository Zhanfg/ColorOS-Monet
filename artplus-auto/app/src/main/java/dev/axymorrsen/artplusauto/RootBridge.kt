package dev.axymorrsen.artplusauto

import android.content.ContentResolver
import android.provider.Settings
import java.io.File
import java.util.concurrent.TimeUnit

internal class RootBridge(
    private val resolver: ContentResolver,
    private val apkPath: String,
) {
    companion object {
        private const val ROOT_DIR = "/data/oplus/uxicons"
        private const val CONFIG_KEY = "key_ux_icon_config"
        private const val DEFAULT_THEME = 2
        private const val INSPIRATION_THEME = 3
        private const val THEME_SHIFT = 4
        private const val ARTPLUS_SHIFT = 8
        private const val THEME_MASK = 0x0fL shl THEME_SHIFT
        private const val ARTPLUS_MASK = 0x07L shl ARTPLUS_SHIFT
        private const val FALLBACK_CONFIG = 2314313028685793584L
    }

    fun isRootAvailable(): Boolean =
        runCatching { runSu("id -u", 4_000).trim().lineSequence().lastOrNull() == "0" }
            .getOrDefault(false)

    fun hasGeneratedPackage(packageName: String): Boolean {
        val target = "$ROOT_DIR/$packageName"
        val cmd = """
            [ -f ${quote("$target/recfg.png")} ] &&
            [ -f ${quote("$target/recbg.png")} ] &&
            [ -f ${quote("$target/rec_night.png")} ] &&
            [ -f ${quote("$target/monochrome.png")} ] &&
            echo yes || true
        """.trimIndent()
        return runCatching { runSu(cmd, 4_000).contains("yes") }.getOrDefault(false)
    }

    fun install(packageName: String, stagingDir: File) {
        val target = "$ROOT_DIR/$packageName"
        val source = stagingDir.absolutePath
        val cmd = """
            set -e
            mkdir -p ${quote(target)}
            find ${quote(source)} -maxdepth 1 -type f -name '*.png' -exec cp -f {} ${quote(target)}/ \;
            find ${quote(target)} -maxdepth 1 -type f -name '*.png' -exec chmod 0644 {} +
            restorecon -RF ${quote(target)} >/dev/null 2>&1 || true
        """.trimIndent()
        runSu(cmd, 12_000)
    }

    fun refreshLauncher(): String {
        val current = Settings.System.getString(resolver, CONFIG_KEY)
            ?.trim()
            ?.toLongOrNull()
            ?: FALLBACK_CONFIG

        val finalTheme = ((current and THEME_MASK) ushr THEME_SHIFT).toInt()
        val tempTheme = if (finalTheme == DEFAULT_THEME) INSPIRATION_THEME else DEFAULT_THEME
        val finalConfig = (current and ARTPLUS_MASK.inv()) or (1L shl ARTPLUS_SHIFT)
        val tempConfig = (finalConfig and THEME_MASK.inv()) or
            ((tempTheme.toLong() and 0x0fL) shl THEME_SHIFT)

        val cli = "dev.axymorrsen.artplusauto.UxConfigPoke"
        val cmd = """
            set -e
            APK=${quote(apkPath)}
            apply_config() {
                value="${'$'}1"
                app_process -Djava.class.path="${'$'}APK" /system/bin $cli "${'$'}value" >/dev/null 2>&1 || true
                settings put system $CONFIG_KEY "${'$'}value"
                am broadcast -a oplus.intent.action.SKIN_CHANGED >/dev/null 2>&1 || true
            }
            apply_config $tempConfig
            sleep 1
            apply_config $finalConfig
            am start -a android.intent.action.MAIN -c android.intent.category.HOME >/dev/null 2>&1 ||
                input keyevent 3 >/dev/null 2>&1 || true
            echo "$tempConfig -> $finalConfig"
        """.trimIndent()
        return runSu(cmd, 15_000).trim()
    }

    private fun runSu(command: String, timeoutMs: Long): String {
        val process = ProcessBuilder("su", "-c", command)
            .redirectErrorStream(true)
            .start()
        val output = StringBuilder()
        val reader = Thread {
            process.inputStream.bufferedReader().useLines { lines ->
                lines.forEach { output.append(it).append('\n') }
            }
        }.apply { start() }

        val finished = process.waitFor(timeoutMs, TimeUnit.MILLISECONDS)
        if (!finished) {
            process.destroyForcibly()
            reader.join(300)
            error("root command timed out")
        }
        reader.join(1_000)
        if (process.exitValue() != 0) {
            error("root command failed (${process.exitValue()}): ${output.toString().trim().take(180)}")
        }
        return output.toString()
    }

    private fun quote(value: String): String =
        "'" + value.replace("'", "'\\''") + "'"
}
