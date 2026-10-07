package dev.axymorrsen.colorosartplus

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedReader
import java.io.InputStreamReader

internal object RootShell {
    data class AdaptedPackages(
        val system: Set<String>,
        val modules: Set<String>,
    )

    suspend fun hasRoot(): Boolean = runCatching {
        exec("id -u").trim() == "0"
    }.getOrDefault(false)

    suspend fun scanAdaptedPackages(): AdaptedPackages = withContext(Dispatchers.IO) {
        val script = """
            emit_pkgs() {
              tag="$1"
              shift
              for root in "$@"; do
                [ -d "$root" ] || continue
                find "$root" -type f -name 'rec_night.png' 2>/dev/null | while IFS= read -r f; do
                  pkg="$(basename "$(dirname "$f")")"
                  case "$pkg" in
                    ''|hdpi|xhdpi|xxhdpi|xxxhdpi) continue ;;
                  esac
                  printf '%s|%s\n' "$tag" "$pkg"
                done
              done
            }

            emit_pkgs SYS \
              /my_product/media/theme/uxicons \
              /product/media/theme/uxicons \
              /system/product/media/theme/uxicons \
              /oplus_product/media/theme/uxicons

            if [ -d /data/adb/modules ]; then
              find /data/adb/modules -type f -name 'rec_night.png' 2>/dev/null | while IFS= read -r f; do
                case "$f" in
                  */uxicons/*/rec_night.png)
                    pkg="$(basename "$(dirname "$f")")"
                    printf 'MOD|%s\n' "$pkg"
                    ;;
                esac
              done
            fi
        """.trimIndent()

        val sys = linkedSetOf<String>()
        val modules = linkedSetOf<String>()
        exec(script).lineSequence().forEach { line ->
            val sep = line.indexOf('|')
            if (sep <= 0 || sep == line.lastIndex) return@forEach
            val tag = line.substring(0, sep)
            val pkg = line.substring(sep + 1).trim()
            if (pkg.isBlank()) return@forEach
            when (tag) {
                "SYS" -> sys += pkg
                "MOD" -> modules += pkg
            }
        }
        AdaptedPackages(sys, modules)
    }

    suspend fun exec(command: String): String = withContext(Dispatchers.IO) {
        val process = ProcessBuilder("su", "-c", command)
            .redirectErrorStream(true)
            .start()

        val output = buildString {
            BufferedReader(InputStreamReader(process.inputStream)).use { reader ->
                while (true) {
                    val line = reader.readLine() ?: break
                    appendLine(line)
                }
            }
        }
        val rc = process.waitFor()
        if (rc != 0) {
            error("su exit=$rc\n$output")
        }
        output
    }
}
