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
                description=Generated ColorOS ART+ dark icon assets. Applied at post-fs-data; original data-side assets are backed up before first replacement.
                """.trimIndent() + "\n",
            )

            textEntry("skip_mount", "")
            textEntry("packages.list", packageDirs.joinToString("\n") { it.name } + "\n")

            val applyScript = """
                apply_assets() {
                  MODDIR="${d}1"
                  TARGET=/data/oplus/uxicons
                  BACKUP=/data/adb/coloros_artplus_auto_backup
                  LEGACY_BACKUP=/data/adb/coloros-monet/artplus-backup/original
                  mkdir -p "${d}TARGET" "${d}BACKUP" 2>/dev/null || true
                  chmod 0700 "${d}BACKUP" 2>/dev/null || true

                  [ -f "${d}MODDIR/packages.list" ] || return 0
                  while IFS= read -r pkg; do
                    [ -n "${d}pkg" ] || continue
                    src="${d}MODDIR/payload/uxicons/${d}pkg"
                    dst="${d}TARGET/${d}pkg"
                    bak="${d}BACKUP/${d}pkg"
                    [ -d "${d}src" ] || continue

                    if [ ! -e "${d}bak/.captured" ]; then
                      mkdir -p "${d}bak"
                      legacy="${d}LEGACY_BACKUP/${d}pkg"
                      if [ -e "${d}legacy/.captured" ]; then
                        find "${d}legacy" -maxdepth 1 -type f ! -name '.captured' -exec cp -f {} "${d}bak"/ \; 2>/dev/null || true
                      elif [ -d "${d}dst" ]; then
                        cp -af "${d}dst"/. "${d}bak"/ 2>/dev/null || true
                      fi
                      touch "${d}bak/.captured"
                    fi

                    mkdir -p "${d}dst"
                    cp -f "${d}src"/*.png "${d}dst"/ 2>/dev/null || true
                    chmod 0644 "${d}dst"/*.png 2>/dev/null || true
                    restorecon -RF "${d}dst" 2>/dev/null || true
                  done < "${d}MODDIR/packages.list"
                }
            """.trimIndent()

            textEntry(
                "customize.sh",
                """
                #!/system/bin/sh
                ui_print "- ColorOS ART+ Auto generated module"
                ui_print "- Generated packages: ${packageDirs.size}"
                ui_print "- Existing ROM/module-adapted packages were skipped by the generator."
                ui_print "- The module applies assets at post-fs-data before Launcher starts."
                ui_print "- Reboot after installation."
                """.trimIndent() + "\n",
            )

            textEntry(
                "post-fs-data.sh",
                """
                #!/system/bin/sh
                MODDIR=${d}{0%/*}
                $applyScript
                apply_assets "${d}MODDIR"
                exit 0
                """.trimIndent() + "\n",
            )

            textEntry(
                "service.sh",
                """
                #!/system/bin/sh
                MODDIR=${d}{0%/*}
                $applyScript
                count=0
                while [ ${d}count -lt 60 ]; do
                  [ -d /data/oplus/uxicons ] && break
                  sleep 1
                  count=${d}((count + 1))
                done
                apply_assets "${d}MODDIR"
                exit 0
                """.trimIndent() + "\n",
            )

            textEntry(
                "action.sh",
                """
                #!/system/bin/sh
                MODDIR=${d}{0%/*}
                $applyScript
                apply_assets "${d}MODDIR"
                am force-stop com.android.launcher >/dev/null 2>&1 || true
                monkey -p com.android.launcher 1 >/dev/null 2>&1 || true
                echo "ART+ assets reapplied. If icons are still cached, reboot once."
                exit 0
                """.trimIndent() + "\n",
            )

            textEntry(
                "uninstall.sh",
                """
                #!/system/bin/sh
                MODDIR=${d}{0%/*}
                TARGET=/data/oplus/uxicons
                BACKUP=/data/adb/coloros_artplus_auto_backup

                if [ -f "${d}MODDIR/packages.list" ]; then
                  while IFS= read -r pkg; do
                    [ -n "${d}pkg" ] || continue
                    dst="${d}TARGET/${d}pkg"
                    bak="${d}BACKUP/${d}pkg"
                    rm -rf "${d}dst"
                    if [ -e "${d}bak/.captured" ]; then
                      mkdir -p "${d}dst"
                      find "${d}bak" -maxdepth 1 -type f ! -name '.captured' -exec cp -f {} "${d}dst"/ \; 2>/dev/null || true
                      if ! find "${d}dst" -maxdepth 1 -type f 2>/dev/null | grep -q .; then
                        rmdir "${d}dst" 2>/dev/null || true
                      else
                        chmod 0644 "${d}dst"/* 2>/dev/null || true
                        restorecon -RF "${d}dst" 2>/dev/null || true
                      fi
                    fi
                  done < "${d}MODDIR/packages.list"
                fi

                rm -rf "${d}BACKUP" 2>/dev/null || true
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
