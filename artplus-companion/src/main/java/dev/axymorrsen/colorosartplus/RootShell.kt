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

    suspend fun restoreAlpha1WritesOnce(): Int = withContext(Dispatchers.IO) {
        val d = '$'
        val script = """
            BASE=/data/adb/coloros-monet/artplus-backup
            LEGACY="${d}BASE/original"
            MARK="${d}BASE/.alpha2_restored"
            TARGET=/data/oplus/uxicons

            if [ -e "${d}MARK" ] || [ ! -d "${d}LEGACY" ]; then
              echo 0
              exit 0
            fi

            count=0
            for bak in "${d}LEGACY"/*; do
              [ -d "${d}bak" ] || continue
              [ -e "${d}bak/.captured" ] || continue
              pkg="${d}(basename "${d}bak")"
              dst="${d}TARGET/${d}pkg"

              rm -rf "${d}dst"
              if find "${d}bak" -maxdepth 1 -type f ! -name '.captured' 2>/dev/null | grep -q .; then
                mkdir -p "${d}dst"
                find "${d}bak" -maxdepth 1 -type f ! -name '.captured' -exec cp -f {} "${d}dst"/ \\; 2>/dev/null || true
                chmod 0644 "${d}dst"/* 2>/dev/null || true
                restorecon -RF "${d}dst" 2>/dev/null || true
              fi

              count=${d}((count + 1))
            done

            mkdir -p "${d}BASE"
            touch "${d}MARK"
            echo "${d}count"
        """.trimIndent()

        exec(script)
            .lineSequence()
            .mapNotNull { it.trim().toIntOrNull() }
            .lastOrNull()
            ?: 0
    }

    suspend fun scanAdaptedPackages(): AdaptedPackages = withContext(Dispatchers.IO) {
        val d = '$'
        val script = """
            emit_pkgs() {
              tag="${d}1"
              shift
              for root in "${d}@"; do
                [ -d "${d}root" ] || continue
                find "${d}root" -type f -name 'rec_night.png' 2>/dev/null | while IFS= read -r f; do
                  pkg="${d}(basename "${d}(dirname "${d}f")")"
                  case "${d}pkg" in
                    ''|hdpi|xhdpi|xxhdpi|xxxhdpi) continue ;;
                  esac
                  printf '%s|%s\n' "${d}tag" "${d}pkg"
                done
              done
            }

            emit_pkgs SYS \
              /my_product/media/theme/uxicons \
              /product/media/theme/uxicons \
              /system/product/media/theme/uxicons \
              /oplus_product/media/theme/uxicons

            if [ -d /data/adb/modules ]; then
              for mod in /data/adb/modules/*; do
                [ -d "${d}mod" ] || continue
                [ -e "${d}mod/disable" ] && continue
                [ -e "${d}mod/remove" ] && continue

                find "${d}mod" -type f -name 'rec_night.png' 2>/dev/null | while IFS= read -r f; do
                  case "${d}f" in
                    */uxicons/*/rec_night.png)
                      pkg="${d}(basename "${d}(dirname "${d}f")")"
                      printf 'MOD|%s\n' "${d}pkg"
                      ;;
                  esac
                done
              done
            fi
        """.trimIndent()

        val system = linkedSetOf<String>()
        val modules = linkedSetOf<String>()

        exec(script).lineSequence().forEach { line ->
            val split = line.indexOf('|')
            if (split <= 0 || split == line.lastIndex) return@forEach

            val tag = line.substring(0, split)
            val pkg = line.substring(split + 1).trim()
            if (pkg.isBlank()) return@forEach

            when (tag) {
                "SYS" -> system += pkg
                "MOD" -> modules += pkg
            }
        }

        AdaptedPackages(
            system = system,
            modules = modules,
        )
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
            error("su exit=${rc}\n${output}")
        }
        output
    }
}
