package dev.axymorrsen.artplusauto

import android.app.Activity
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import java.util.Locale
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private val worker = Executors.newSingleThreadExecutor()
    private lateinit var status: TextView
    private lateinit var button: Button
    private lateinit var progress: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val pad = (20 * resources.displayMetrics.density).toInt()
        val rootLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            setBackgroundColor(Color.rgb(247, 247, 247))
        }

        rootLayout.addView(TextView(this).apply {
            text = "ColorOS 17 · ART+ Auto Compiler"
            textSize = 24f
            setTextColor(Color.rgb(28, 28, 30))
        })

        rootLayout.addView(TextView(this).apply {
            text = "Adaptive Icon 原生取层；旧式图标自动分层；低置信度自动保守回退。仅处理用户安装的 Launcher 应用。"
            textSize = 14f
            setTextColor(Color.rgb(80, 80, 86))
            setPadding(0, pad / 2, 0, pad)
        })

        button = Button(this).apply {
            text = "一键生成并应用"
            setOnClickListener { startCompile() }
        }
        rootLayout.addView(button)

        progress = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            visibility = View.GONE
            max = 100
        }
        rootLayout.addView(progress)

        status = TextView(this).apply {
            text = "等待开始。\n"
            textSize = 13f
            setTextColor(Color.rgb(52, 52, 54))
            setTextIsSelectable(true)
        }
        val scroll = ScrollView(this).apply {
            addView(status)
            isFillViewport = true
        }
        rootLayout.addView(
            scroll,
            LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f,
            ).apply { topMargin = pad / 2 },
        )

        setContentView(rootLayout)
    }

    private fun startCompile() {
        button.isEnabled = false
        progress.visibility = View.VISIBLE
        progress.progress = 0
        status.text = "正在检查 Root…\n"

        worker.execute {
            val root = RootBridge(contentResolver, applicationInfo.sourceDir)
            if (!root.isRootAvailable()) {
                postLine("未获得 Root，已停止。")
                finishUi()
                return@execute
            }

            val targets = queryTargets()
            if (targets.isEmpty()) {
                postLine("没有找到可处理的用户 Launcher 应用。")
                finishUi()
                return@execute
            }

            postLine("发现 ${targets.size} 个用户 Launcher 应用。")
            val compiler = ArtPlusCompiler(this, root)
            val prefs = getSharedPreferences("compiler-cache", MODE_PRIVATE)
            var generated = 0
            var skipped = 0
            var failed = 0

            targets.forEachIndexed { index, info ->
                val pkg = info.packageName
                try {
                    val signature = buildString {
                        append(versionCodeOf(pkg))
                        append(':')
                        append(info.iconResource)
                        append(':')
                        append(ArtPlusSpec.GENERATOR_VERSION)
                    }
                    val cacheKey = "sig:$pkg"
                    if (prefs.getString(cacheKey, null) == signature && root.hasGeneratedPackage(pkg)) {
                        skipped++
                        postLine("SKIP  $pkg")
                    } else {
                        val result = compiler.compileAndInstall(info)
                        prefs.edit().putString(cacheKey, signature).apply()
                        generated++
                        postLine(
                            "OK    ${result.packageName}  " +
                                "${result.provenance}  confidence=${
                                    String.format(Locale.US, "%.2f", result.confidence)
                                }",
                        )
                    }
                } catch (t: Throwable) {
                    failed++
                    postLine("FAIL  $pkg  ${t.message ?: t.javaClass.simpleName}")
                }
                val percent = ((index + 1) * 100 / targets.size).coerceIn(0, 100)
                runOnUiThread { progress.progress = percent }
            }

            val refresh = runCatching { root.refreshLauncher() }
                .fold(
                    onSuccess = { "刷新完成：$it" },
                    onFailure = { "资源已写入，但桌面热刷新失败：${it.message}" },
                )
            postLine(refresh)
            postLine("完成：生成 $generated，缓存跳过 $skipped，失败 $failed。")
            finishUi()
        }
    }

    private fun queryTargets(): List<android.content.pm.ActivityInfo> {
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        val flags = PackageManager.ResolveInfoFlags.of(PackageManager.MATCH_ALL.toLong())
        return packageManager.queryIntentActivities(intent, flags)
            .asSequence()
            .mapNotNull { it.activityInfo }
            .filter { it.packageName != packageName }
            .filter {
                (it.applicationInfo.flags and ApplicationInfo.FLAG_SYSTEM) == 0
            }
            .distinctBy { it.packageName }
            .sortedBy { it.packageName }
            .toList()
    }

    private fun versionCodeOf(pkg: String): Long =
        runCatching {
            packageManager.getPackageInfo(
                pkg,
                PackageManager.PackageInfoFlags.of(0),
            ).longVersionCode
        }.getOrDefault(0L)

    private fun postLine(line: String) {
        runOnUiThread {
            status.append(line)
            status.append("\n")
        }
    }

    private fun finishUi() {
        runOnUiThread {
            progress.visibility = View.GONE
            button.isEnabled = true
        }
    }

    override fun onDestroy() {
        worker.shutdownNow()
        super.onDestroy()
    }
}
