package dev.axymorrsen.colorosartplus

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedInputStream
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.zip.ZipEntry
import java.util.zip.ZipFile
import java.util.zip.ZipOutputStream

internal object ModuleExporter {
    internal data class ExportResult(
        val displayName: String,
        val uri: Uri,
        val handlerLabels: List<String>,
    )

    suspend fun buildAndPublish(
        context: Context,
        generatedRoot: File,
    ): ExportResult = withContext(Dispatchers.IO) {
        val packageDirs = generatedRoot.listFiles()
            ?.filter { it.isDirectory }
            ?.sortedBy { it.name }
            .orEmpty()

        require(packageDirs.isNotEmpty()) { "没有可打包的生成结果" }

        val stamp = SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US).format(Date())
        val displayName = "ColorOS-ARTPlus-Auto-Generated-$stamp.zip"
        val tempZip = File(context.cacheDir, displayName)
        val d = '$'

        ZipOutputStream(BufferedOutputStream(FileOutputStream(tempZip))).use { zip ->
            fun textEntry(name: String, text: String) {
                zip.putNextEntry(ZipEntry(name))
                zip.write(text.toByteArray(Charsets.UTF_8))
                zip.closeEntry()
            }

            val versionCode = (System.currentTimeMillis() / 1000L)
                .coerceAtMost(Int.MAX_VALUE.toLong())
                .toInt()

            textEntry(
                "module.prop",
                """
                id=coloros_artplus_auto_generated
                name=ColorOS ART+ Auto · Generated Icons
                version=generated-$stamp
                versionCode=$versionCode
                author=ColorOS ART+ Auto
                description=Generated ColorOS ART+ icon assets. Uses bind mounts only; it does not overwrite /data/oplus/uxicons contents.
                """.trimIndent() + "\n",
            )

            textEntry("skip_mount", "")
            textEntry("packages.list", packageDirs.joinToString("\n") { it.name } + "\n")

            val mountScript = """
                mount_assets() {
                  MODDIR="${d}1"
                  TARGET=/data/oplus/uxicons

                  [ -f "${d}MODDIR/packages.list" ] || return 0
                  mkdir -p "${d}TARGET" 2>/dev/null || true

                  while IFS= read -r pkg; do
                    [ -n "${d}pkg" ] || continue
                    src="${d}MODDIR/payload/uxicons/${d}pkg"
                    dst="${d}TARGET/${d}pkg"
                    [ -d "${d}src" ] || continue

                    mkdir -p "${d}dst" 2>/dev/null || true

                    mounted_root="${d}(awk -v p="${d}dst" '${d}5 == p { root=${d}4 } END { if (root != "") print root }' /proc/self/mountinfo 2>/dev/null)"
                    case "${d}mounted_root" in
                      /adb/*) mounted_root="/data${d}mounted_root" ;;
                    esac
                    if [ -n "${d}mounted_root" ]; then
                      case "${d}mounted_root" in
                        "${d}src")
                          umount "${d}dst" 2>/dev/null || umount -l "${d}dst" 2>/dev/null || true
                          ;;
                        *)
                          echo "ARTPLUS_CONFLICT_SKIP|${d}pkg|${d}mounted_root"
                          continue
                          ;;
                      esac
                    fi

                    mount --bind "${d}src" "${d}dst" 2>/dev/null \
                      || busybox mount --bind "${d}src" "${d}dst" 2>/dev/null \
                      || toybox mount --bind "${d}src" "${d}dst" 2>/dev/null \
                      || echo "ARTPLUS_MOUNT_FAILED|${d}pkg"
                  done < "${d}MODDIR/packages.list"
                }
            """.trimIndent()

            textEntry(
                "customize.sh",
                """
                #!/system/bin/sh
                ui_print "- ColorOS ART+ Auto generated module"
                ui_print "- Generated packages: ${packageDirs.size}"
                ui_print "- Bind-mount mode: no direct writes to /data/oplus/uxicons assets"
                ui_print "- Existing system/external-module adaptations were skipped by the generator."
                ui_print "- Reboot after installation."
                """.trimIndent() + "\n",
            )

            textEntry(
                "post-fs-data.sh",
                """
                #!/system/bin/sh
                MODDIR=${d}{0%/*}
                $mountScript
                mount_assets "${d}MODDIR"
                exit 0
                """.trimIndent() + "\n",
            )

            textEntry(
                "service.sh",
                """
                #!/system/bin/sh
                MODDIR=${d}{0%/*}
                $mountScript

                count=0
                while [ ${d}count -lt 60 ]; do
                  [ -d /data/oplus/uxicons ] && break
                  sleep 1
                  count=${d}((count + 1))
                done

                mount_assets "${d}MODDIR"
                exit 0
                """.trimIndent() + "\n",
            )

            textEntry(
                "action.sh",
                """
                #!/system/bin/sh
                MODDIR=${d}{0%/*}
                $mountScript
                mount_assets "${d}MODDIR"
                am force-stop com.android.launcher >/dev/null 2>&1 || true
                monkey -p com.android.launcher 1 >/dev/null 2>&1 || input keyevent KEYCODE_HOME >/dev/null 2>&1 || true
                echo "ART+ bind mounts reapplied."
                exit 0
                """.trimIndent() + "\n",
            )

            textEntry(
                "uninstall.sh",
                """
                #!/system/bin/sh
                MODDIR=${d}{0%/*}
                TARGET=/data/oplus/uxicons

                if [ -f "${d}MODDIR/packages.list" ]; then
                  while IFS= read -r pkg; do
                    [ -n "${d}pkg" ] || continue
                    dst="${d}TARGET/${d}pkg"
                    src="${d}MODDIR/payload/uxicons/${d}pkg"
                    mounted_root="${d}(awk -v p="${d}dst" '${d}5 == p { root=${d}4 } END { if (root != "") print root }' /proc/self/mountinfo 2>/dev/null)"
                    case "${d}mounted_root" in
                      /adb/*) mounted_root="/data${d}mounted_root" ;;
                    esac
                    if [ "${d}mounted_root" = "${d}src" ]; then
                      umount "${d}dst" 2>/dev/null || umount -l "${d}dst" 2>/dev/null || true
                    fi
                  done < "${d}MODDIR/packages.list"
                fi

                am force-stop com.android.launcher >/dev/null 2>&1 || true
                exit 0
                """.trimIndent() + "\n",
            )

            packageDirs.forEach { pkgDir ->
                pkgDir.listFiles()
                    ?.filter { it.isFile && it.extension.equals("png", ignoreCase = true) }
                    ?.sortedBy { it.name }
                    ?.forEach { file ->
                        val entry = ZipEntry("payload/uxicons/${pkgDir.name}/${file.name}")
                        zip.putNextEntry(entry)
                        BufferedInputStream(FileInputStream(file)).use { input ->
                            input.copyTo(zip)
                        }
                        zip.closeEntry()
                    }
            }
        }

        validateModuleZip(tempZip, packageDirs.map { it.name })
        val uri = publishToDownloads(context, tempZip, displayName)
        val handlers = resolveZipHandlers(context, uri)
        tempZip.delete()
        ExportResult(displayName, uri, handlers)
    }

    private fun validateModuleZip(zipFile: File, packages: List<String>) {
        ZipFile(zipFile).use { zip ->
            val names = zip.entries().asSequence().map { it.name }.toSet()
            val requiredRoot = setOf(
                "module.prop",
                "skip_mount",
                "packages.list",
                "post-fs-data.sh",
                "service.sh",
                "action.sh",
                "uninstall.sh",
            )
            val missingRoot = requiredRoot - names
            check(missingRoot.isEmpty()) {
                "模块结构缺失: ${missingRoot.joinToString()}"
            }

            val requiredAssets = listOf(
                "recfg.png",
                "recbg.png",
                "rec_night.png",
                "monochrome.png",
            )
            packages.forEach { pkg ->
                requiredAssets.forEach { asset ->
                    val path = "payload/uxicons/${pkg}/${asset}"
                    check(path in names) {
                        "模块资源缺失: ${path}"
                    }
                }
            }
        }
    }

    private fun publishToDownloads(context: Context, source: File, displayName: String): Uri {
        check(Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            "当前实现要求 Android 10 或更高版本"
        }

        val resolver = context.contentResolver
        val values = ContentValues().apply {
            put(MediaStore.Downloads.DISPLAY_NAME, displayName)
            put(MediaStore.Downloads.MIME_TYPE, "application/zip")
            put(
                MediaStore.Downloads.RELATIVE_PATH,
                Environment.DIRECTORY_DOWNLOADS + "/ColorOS-ARTPlus-Auto",
            )
            put(MediaStore.Downloads.IS_PENDING, 1)
        }
        val uri = requireNotNull(
            resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values),
        ) { "无法在 Downloads 中创建模块文件" }

        try {
            requireNotNull(resolver.openOutputStream(uri, "w")).use { output ->
                BufferedInputStream(FileInputStream(source)).use { input ->
                    input.copyTo(output)
                }
            }
            val ready = ContentValues().apply {
                put(MediaStore.Downloads.IS_PENDING, 0)
            }
            resolver.update(uri, ready, null, null)
            return uri
        } catch (t: Throwable) {
            resolver.delete(uri, null, null)
            throw t
        }
    }

    fun buildViewIntent(uri: Uri): Intent =
        Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/zip")
            addCategory(Intent.CATEGORY_DEFAULT)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }

    fun resolveZipHandlers(context: Context, uri: Uri): List<String> {
        val intent = buildViewIntent(uri)
        return context.packageManager
            .queryIntentActivities(intent, PackageManager.MATCH_DEFAULT_ONLY)
            .map { info ->
                runCatching { info.loadLabel(context.packageManager).toString() }
                    .getOrDefault(info.activityInfo.packageName)
            }
            .distinct()
    }
}
