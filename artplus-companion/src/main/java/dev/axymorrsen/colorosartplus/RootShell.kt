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

            is_mount() {
              p="${d}1"
              awk -v p="${d}p" '${d}5 == p { found=1 } END { exit(found ? 0 : 1) }' /proc/self/mountinfo 2>/dev/null
            }

            mount_source() {
              p="${d}1"
              root="${d}(awk -v p="${d}p" '${d}5 == p { root=${d}4 } END { if (root != "") print root }' /proc/self/mountinfo 2>/dev/null)"
              case "${d}root" in
                /adb/*) echo "/data${d}root" ;;
                *) echo "${d}root" ;;
              esac
            }

            remove_known() {
              dir="${d}1"
              [ -d "${d}dir" ] || return 0
              for name in ${d}KNOWN; do
                rm -f "${d}dir/${d}name" 2>/dev/null || true
              done
            }

            copy_backup() {
              srcdir="${d}1"
              dstdir="${d}2"
              mkdir -p "${d}dstdir" 2>/dev/null || true
              for src in "${d}srcdir"/*; do
                [ -f "${d}src" ] || continue
                [ "${d}(basename "${d}src")" = ".captured" ] && continue
                cp -f "${d}src" "${d}dstdir/" 2>/dev/null || return 1
              done
              return 0
            }

            am force-stop com.android.launcher >/dev/null 2>&1 || true

            count=0
            for bak in "${d}BASE"/*; do
              [ -d "${d}bak" ] || continue
              [ -e "${d}bak/.captured" ] || continue

              pkg="${d}(basename "${d}bak")"
              dst="${d}TARGET/${d}pkg"
              srcroot=""

              if is_mount "${d}dst"; then
                srcroot="${d}(mount_source "${d}dst")"

                case "${d}srcroot" in
                  /data/adb/modules/*|/data/adb/modules_update/*)
                    if [ -d "${d}srcroot" ]; then
                      remove_known "${d}srcroot"
                      copy_backup "${d}bak" "${d}srcroot" || true
                      chmod 0644 "${d}srcroot"/*.png 2>/dev/null || true
                      restorecon -RF "${d}srcroot" 2>/dev/null || true
                    fi
                    ;;
                esac

                tries=0
                while is_mount "${d}dst" && [ "${d}tries" -lt 8 ]; do
                  umount "${d}dst" 2>/dev/null || umount -l "${d}dst" 2>/dev/null || break
                  tries=${d}((tries + 1))
                done
              fi

              mkdir -p "${d}dst" 2>/dev/null || true
              remove_known "${d}dst"
              copy_backup "${d}bak" "${d}dst" || true

              if ls "${d}dst"/*.png >/dev/null 2>&1; then
                chmod 0644 "${d}dst"/*.png 2>/dev/null || true
                restorecon -RF "${d}dst" 2>/dev/null || true
              else
                rmdir "${d}dst" 2>/dev/null || true
              fi

              if [ -n "${d}srcroot" ] && [ -d "${d}srcroot" ]; then
                mkdir -p "${d}dst" 2>/dev/null || true
                mount --bind "${d}srcroot" "${d}dst" 2>/dev/null \
                  || busybox mount --bind "${d}srcroot" "${d}dst" 2>/dev/null \
                  || toybox mount --bind "${d}srcroot" "${d}dst" 2>/dev/null \
                  || true
              fi

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
