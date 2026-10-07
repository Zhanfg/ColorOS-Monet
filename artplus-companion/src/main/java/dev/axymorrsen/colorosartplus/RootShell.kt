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
        val d = '$'
        val script = """
            own_id=coloros_artplus_auto_generated
            own_list=/data/adb/modules/${d}own_id/packages.list

            is_own_pkg() {
              pkg="${d}1"
              [ -f "${d}own_list" ] || return 1
              grep -Fqx "${d}pkg" "${d}own_list" 2>/dev/null
            }

            emit_system_pkgs() {
              for root in "${d}@"; do
                [ -d "${d}root" ] || continue
                find "${d}root" -type f -name 'rec_night.png' 2>/dev/null | while IFS= read -r f; do
                  pkg="${d}(basename "${d}(dirname "${d}f")")"
                  case "${d}pkg" in
                    ''|hdpi|xhdpi|xxhdpi|xxxhdpi) continue ;;
                  esac
                  printf 'SYS|%s\n' "${d}pkg"
                done
              done
            }

            emit_system_pkgs \
              /my_product/media/theme/uxicons \
              /product/media/theme/uxicons \
              /system/product/media/theme/uxicons \
              /oplus_product/media/theme/uxicons

            # Enabled third-party Root modules that already carry rec_night assets.
            if [ -d /data/adb/modules ]; then
              for mod in /data/adb/modules/*; do
                [ -d "${d}mod" ] || continue
                [ -e "${d}mod/disable" ] && continue
                [ -e "${d}mod/remove" ] && continue

                modid="${d}(basename "${d}mod")"
                [ "${d}modid" = "${d}own_id" ] && continue

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

            # Anything already active in the live ColorOS data tree is considered adapted,
            # except packages owned by our previous generated module. This catches bind mounts
            # whose source layout is not recognizable from /data/adb/modules.
            if [ -d /data/oplus/uxicons ]; then
              for f in /data/oplus/uxicons/*/rec_night.png; do
                [ -f "${d}f" ] || continue
                pkg="${d}(basename "${d}(dirname "${d}f")")"
                is_own_pkg "${d}pkg" && continue
                printf 'MOD|%s\n' "${d}pkg"
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

        AdaptedPackages(system = system, modules = modules)
    }

    suspend fun restoreLegacyAlpha1Safely(): Int = withContext(Dispatchers.IO) {
        val d = '$'
        val script = """
            BASE=/data/adb/coloros-monet/artplus-backup/original
            TARGET=/data/oplus/uxicons
            OUR=/data/adb/modules/coloros_artplus_auto_generated
            KNOWN='recfg.png recbg.png rec_night.png monochrome.png monochrome_light.png monochrome_dark.png recfg_1x2.png recfg_2x1.png recfg_2x2.png recbg_1x2.png recbg_2x1.png recbg_2x2.png rec_night_1x2.png rec_night_2x1.png rec_night_2x2.png monochrome_1x2.png monochrome_2x1.png monochrome_2x2.png'

            [ -d "${d}BASE" ] || { echo 0; exit 0; }

            [ -d "${d}OUR" ] && touch "${d}OUR/disable" 2>/dev/null || true
            rm -rf /data/adb/modules_update/coloros_artplus_auto_generated 2>/dev/null || true

            am force-stop com.android.launcher >/dev/null 2>&1 || true

            count=0
            for bak in "${d}BASE"/*; do
              [ -d "${d}bak" ] || continue
              [ -e "${d}bak/.captured" ] || continue

              pkg="${d}(basename "${d}bak")"
              dst="${d}TARGET/${d}pkg"
              mkdir -p "${d}dst" 2>/dev/null || true

              ok=1
              for name in ${d}KNOWN; do
                rm -f "${d}dst/${d}name" 2>/dev/null || ok=0
              done

              if find "${d}bak" -maxdepth 1 -type f ! -name '.captured' 2>/dev/null | grep -q .; then
                while IFS= read -r src; do
                  cp -f "${d}src" "${d}dst/" 2>/dev/null || ok=0
                done <<EOF_RESTORE
${d}(find "${d}bak" -maxdepth 1 -type f ! -name '.captured' 2>/dev/null)
EOF_RESTORE
              fi

              if [ "${d}ok" -ne 1 ]; then
                umount "${d}dst" 2>/dev/null || umount -l "${d}dst" 2>/dev/null || true
                mkdir -p "${d}dst" 2>/dev/null || true
                for name in ${d}KNOWN; do
                  rm -f "${d}dst/${d}name" 2>/dev/null || true
                done

                if find "${d}bak" -maxdepth 1 -type f ! -name '.captured' 2>/dev/null | grep -q .; then
                  find "${d}bak" -maxdepth 1 -type f ! -name '.captured' | while IFS= read -r src; do
                    cp -f "${d}src" "${d}dst/" 2>/dev/null || true
                  done
                else
                  rmdir "${d}dst" 2>/dev/null || true
                fi
              fi

              chmod 0644 "${d}dst"/*.png 2>/dev/null || true
              restorecon -RF "${d}dst" 2>/dev/null || true
              count=${d}((count + 1))
            done

            rm -f /data/adb/coloros-monet/artplus-backup/.alpha2_restored 2>/dev/null || true
            am force-stop com.android.launcher >/dev/null 2>&1 || true
            monkey -p com.android.launcher 1 >/dev/null 2>&1 || input keyevent KEYCODE_HOME >/dev/null 2>&1 || true

            echo "${d}count"
        """.trimIndent()

        exec(script)
            .lineSequence()
            .mapNotNull { it.trim().toIntOrNull() }
            .lastOrNull()
            ?: 0
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
