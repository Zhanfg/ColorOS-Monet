package dev.axymorrsen.colorosartplus

import android.content.ActivityNotFoundException
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.DarkMode
import androidx.compose.material.icons.rounded.Security
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle

class MainActivity : ComponentActivity() {
    private val viewModel: GeneratorViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            ArtPlusTheme {
                val state by viewModel.state.collectAsStateWithLifecycle()

                LaunchedEffect(Unit) {
                    viewModel.installerRequests.collect { uri ->
                        openRootManager(uri)
                    }
                }

                GeneratorScreen(
                    state = state,
                    onStart = viewModel::startGeneration,
                    onApprove = viewModel::approveCurrent,
                    onReject = viewModel::rejectCurrent,
                    onRegenerate = viewModel::regenerateCurrentToggleInvert,
                    onPrevious = viewModel::previousReview,
                    onNext = viewModel::nextReview,
                    onExportApproved = viewModel::exportApproved,
                    onRecoverLegacy = viewModel::recoverLegacyAlpha1,
                    onOpenInstaller = viewModel::requestInstallerAgain,
                )
            }
        }
    }

    private fun openRootManager(uri: Uri) {
        val base = ModuleExporter.buildViewIntent(uri)
        val handlers = packageManager.queryIntentActivities(
            base,
            android.content.pm.PackageManager.MATCH_DEFAULT_ONLY,
        )

        val preferred = handlers.firstOrNull {
            it.activityInfo.packageName == "me.weishu.kernelsu"
        } ?: handlers.firstOrNull {
            it.activityInfo.packageName == "me.bmax.apatch"
        } ?: handlers.firstOrNull {
            runCatching { it.loadLabel(packageManager).toString() }
                .getOrDefault("")
                .contains("Magisk", ignoreCase = true)
        }

        try {
            when {
                preferred != null -> {
                    startActivity(
                        Intent(base).setPackage(preferred.activityInfo.packageName),
                    )
                }

                handlers.isNotEmpty() -> {
                    startActivity(
                        Intent.createChooser(base, "选择 Root 管理器刷入模块"),
                    )
                }

                else -> {
                    val managerPackages = listOf(
                        "me.weishu.kernelsu",
                        "me.bmax.apatch",
                        "com.topjohnwu.magisk",
                    )
                    val launcher = managerPackages.firstNotNullOfOrNull { pkg ->
                        packageManager.getLaunchIntentForPackage(pkg)
                    }
                    if (launcher != null) {
                        startActivity(launcher)
                    } else {
                        startActivity(Intent.createChooser(base, "打开模块 ZIP"))
                    }
                }
            }
        } catch (_: ActivityNotFoundException) {
            // Module remains in Downloads and can be opened from the fallback button.
        }
    }
}

@Composable
private fun ArtPlusTheme(content: @Composable () -> Unit) {
    val context = LocalContext.current
    val dark = isSystemInDarkTheme()
    val colors = when {
        Build.VERSION.SDK_INT >= 31 && dark -> dynamicDarkColorScheme(context)
        Build.VERSION.SDK_INT >= 31 && !dark -> dynamicLightColorScheme(context)
        dark -> darkColorScheme()
        else -> lightColorScheme()
    }
    MaterialTheme(
        colorScheme = colors,
        content = content,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun GeneratorScreen(
    state: GeneratorUiState,
    onStart: () -> Unit,
    onApprove: () -> Unit,
    onReject: () -> Unit,
    onRegenerate: () -> Unit,
    onPrevious: () -> Unit,
    onNext: () -> Unit,
    onExportApproved: () -> Unit,
    onRecoverLegacy: () -> Unit,
    onOpenInstaller: () -> Unit,
) {
    val busy = state.phase in setOf(
        WorkPhase.RequestingRoot,
        WorkPhase.Scanning,
        WorkPhase.Generating,
        WorkPhase.Packaging,
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "ART+ Auto",
                            fontWeight = FontWeight.SemiBold,
                        )
                        Text(
                            text = "ColorOS 17 暗色图标生成器",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                },
            )
        },
    ) { inner ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(inner)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            StatusCard(state)
            ProgressCard(state)

            if (state.phase == WorkPhase.Reviewing ||
                state.phase == WorkPhase.ReadyToFlash
            ) {
                ReviewCard(
                    state = state,
                    onApprove = onApprove,
                    onReject = onReject,
                    onRegenerate = onRegenerate,
                    onPrevious = onPrevious,
                    onNext = onNext,
                    onExportApproved = onExportApproved,
                )
            } else {
                PreviewCard(state.current)
            }

            if (state.module != null) {
                ModuleCard(
                    state = state,
                    onOpenInstaller = onOpenInstaller,
                )
            }

            if (state.phase != WorkPhase.Reviewing &&
                state.phase != WorkPhase.ReadyToFlash
            ) {
                Button(
                    onClick = onStart,
                    enabled = !busy,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    if (busy) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(18.dp),
                            strokeWidth = 2.dp,
                        )
                        Spacer(Modifier.size(10.dp))
                        Text("处理中…")
                    } else {
                        Icon(Icons.Rounded.AutoAwesome, contentDescription = null)
                        Spacer(Modifier.size(8.dp))
                        Text("申请 Root 并生成草稿")
                    }
                }
            }

            OutlinedButton(
                onClick = onRecoverLegacy,
                enabled = !busy,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("安全恢复旧版直接写入")
            }

            Text(
                text = "恢复只处理 ART+ Auto alpha1 备份；不会禁用你的其他图标模块，也不会删除挂载点。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            LogCard(state.logLines)
            Spacer(Modifier.height(18.dp))
        }
    }
}

@Composable
private fun StatusCard(state: GeneratorUiState) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceContainer,
        ),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                imageVector = when {
                    state.hasRoot -> Icons.Rounded.Security
                    state.phase == WorkPhase.Failed -> Icons.Rounded.Warning
                    else -> Icons.Rounded.DarkMode
                },
                contentDescription = null,
                tint = when {
                    state.hasRoot -> MaterialTheme.colorScheme.primary
                    state.phase == WorkPhase.Failed -> MaterialTheme.colorScheme.error
                    else -> MaterialTheme.colorScheme.onSurfaceVariant
                },
            )
            Spacer(Modifier.size(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = state.rootMessage,
                    fontWeight = FontWeight.Medium,
                )
                Text(
                    text = phaseLabel(state.phase),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                state.error?.let {
                    Text(
                        text = it,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
            }
        }
    }
}

@Composable
private fun ProgressCard(state: GeneratorUiState) {
    val c = state.counters
    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text("生成进度", fontWeight = FontWeight.SemiBold)
                Text(
                    if (c.total > 0) "${c.processed} / ${c.total}" else "—",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            LinearProgressIndicator(
                progress = { c.progress },
                modifier = Modifier.fillMaxWidth(),
            )

            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                AssistChip(
                    onClick = {},
                    label = { Text("生成 ${c.generated}") },
                    leadingIcon = {
                        Icon(
                            Icons.Rounded.CheckCircle,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                        )
                    },
                )
                AssistChip(
                    onClick = {},
                    label = { Text("系统跳过 ${c.skippedSystem}") },
                )
                AssistChip(
                    onClick = {},
                    label = { Text("模块跳过 ${c.skippedModule}") },
                )
            }

            if (c.conservative > 0 || c.failed > 0) {
                Text(
                    text = "保守回退 ${c.conservative} · 失败 ${c.failed}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun ReviewCard(
    state: GeneratorUiState,
    onApprove: () -> Unit,
    onReject: () -> Unit,
    onRegenerate: () -> Unit,
    onPrevious: () -> Unit,
    onNext: () -> Unit,
    onExportApproved: () -> Unit,
) {
    val item = state.currentReview
    val summary = state.reviewSummary

    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceContainer,
        ),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text("逐个审核", fontWeight = FontWeight.SemiBold)
                Text(
                    if (summary.total > 0) {
                        "${state.reviewIndex + 1} / ${summary.total}"
                    } else {
                        "—"
                    },
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            Text(
                "待确认 ${summary.pending} · 已通过 ${summary.approved} · 已拒绝 ${summary.rejected}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            if (item == null) {
                Text(
                    "当前没有可审核的草稿。",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                return@Column
            }

            Column {
                Text(
                    item.label,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    item.packageName,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                PreviewTile(
                    title = "原图",
                    bitmap = item.original,
                    modifier = Modifier.weight(1f),
                )
                PreviewTile(
                    title = "生成草稿",
                    bitmap = item.generated,
                    modifier = Modifier.weight(1f),
                )
            }

            Surface(
                shape = RoundedCornerShape(14.dp),
                color = MaterialTheme.colorScheme.surfaceContainerHigh,
            ) {
                Column(
                    modifier = Modifier.padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                ) {
                    Text(
                        text = "策略：${generationStrategyLabel(item.strategy)}",
                        style = MaterialTheme.typography.bodySmall,
                    )
                    Text(
                        text = buildString {
                            append("置信度 ")
                            append((item.confidence * 100f).toInt())
                            append("%")
                            if (item.flipped) append(" · 已自动反相")
                            append(" · ")
                            append(reviewDecisionLabel(item.decision))
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                OutlinedButton(
                    onClick = onPrevious,
                    enabled = state.reviewIndex > 0,
                    modifier = Modifier.weight(1f),
                ) {
                    Text("上一个")
                }
                OutlinedButton(
                    onClick = onNext,
                    enabled = state.reviewIndex < state.reviewItems.lastIndex,
                    modifier = Modifier.weight(1f),
                ) {
                    Text("下一个")
                }
            }

            OutlinedButton(
                onClick = onRegenerate,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(
                    if (item.strategy == GenerationStrategy.DarkDominantInvert) {
                        "关闭反相并重新生成"
                    } else {
                        "强制反相并重新生成"
                    },
                )
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                OutlinedButton(
                    onClick = onReject,
                    modifier = Modifier.weight(1f),
                ) {
                    Text("拒绝")
                }
                Button(
                    onClick = onApprove,
                    modifier = Modifier.weight(1f),
                ) {
                    Text("通过")
                }
            }

            Button(
                onClick = onExportApproved,
                enabled = summary.approved > 0 &&
                    state.phase != WorkPhase.Packaging,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("导出已确认项（${summary.approved}）")
            }

            Text(
                "未确认和已拒绝图标不会进入模块；导出后也不会自动刷入。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun PreviewCard(frame: PreviewFrame?) {
    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("实时预览", fontWeight = FontWeight.SemiBold)

            if (frame == null) {
                Text(
                    "开始生成后，这里会显示当前应用的原图与暗色结果。",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                return@Column
            }

            Column {
                Text(
                    frame.label,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    frame.packageName,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    statusLabel(frame.status),
                    style = MaterialTheme.typography.labelMedium,
                    color = statusColor(frame.status),
                )
            }

            if (frame.original != null && frame.generated != null) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    PreviewTile(
                        title = "原图",
                        bitmap = frame.original,
                        modifier = Modifier.weight(1f),
                    )
                    PreviewTile(
                        title = "暗色结果",
                        bitmap = frame.generated,
                        modifier = Modifier.weight(1f),
                    )
                }
            } else {
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = MaterialTheme.colorScheme.surfaceContainerHigh,
                ) {
                    Text(
                        text = when (frame.status) {
                            ItemStatus.SystemAdapted -> "系统已有完整 ART+ 暗色资源，本次跳过。"
                            ItemStatus.ModuleAdapted -> "现有 Root 模块中已包含暗色资源，本次跳过。"
                            ItemStatus.Failed -> "当前应用生成失败，已继续处理下一项。"
                            else -> "无需预览。"
                        },
                        modifier = Modifier.padding(14.dp),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }
    }
}

@Composable
private fun PreviewTile(
    title: String,
    bitmap: Bitmap,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(132.dp)
                .clip(RoundedCornerShape(22.dp))
                .background(MaterialTheme.colorScheme.surfaceContainerHigh),
            contentAlignment = Alignment.Center,
        ) {
            Image(
                bitmap = bitmap.asImageBitmap(),
                contentDescription = title,
                modifier = Modifier.size(96.dp),
            )
        }
        Text(
            title,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun ModuleCard(
    state: GeneratorUiState,
    onOpenInstaller: () -> Unit,
) {
    val module = state.module ?: return
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer,
        ),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(
                "模块已生成",
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
            )
            Text(
                module.displayName,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
            )
            Text(
                "包含 ${module.generatedPackageCount} 个新适配；已保存到 Download/ColorOS-ARTPlus-Auto。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
            )

            if (state.managerHandlers.isNotEmpty()) {
                Text(
                    "可用安装器：${state.managerHandlers.joinToString("、")}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                )
            }

            Button(
                onClick = onOpenInstaller,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("打开 Root 管理器刷入模块")
            }
        }
    }
}

@Composable
private fun LogCard(lines: List<String>) {
    if (lines.isEmpty()) return
    Card {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text("最近处理", fontWeight = FontWeight.SemiBold)
            lines.takeLast(8).forEach { line ->
                Text(
                    text = line,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun statusColor(status: ItemStatus) = when (status) {
    ItemStatus.Failed -> MaterialTheme.colorScheme.error
    ItemStatus.SystemAdapted,
    ItemStatus.ModuleAdapted -> MaterialTheme.colorScheme.tertiary
    else -> MaterialTheme.colorScheme.primary
}

private fun statusLabel(status: ItemStatus): String = when (status) {
    ItemStatus.SystemAdapted -> "系统已适配 · 跳过"
    ItemStatus.ModuleAdapted -> "已有模块适配 · 跳过"
    ItemStatus.GeneratedAdaptive -> "原生 Adaptive 分层 · 已生成"
    ItemStatus.GeneratedLegacy -> "Legacy 智能拆层 · 已生成"
    ItemStatus.ConservativeFallback -> "低置信度 · 保守生成"
    ItemStatus.Failed -> "生成失败"
}

private fun phaseLabel(phase: WorkPhase): String = when (phase) {
    WorkPhase.Idle -> "等待开始"
    WorkPhase.RequestingRoot -> "Root 授权"
    WorkPhase.Scanning -> "扫描已有适配"
    WorkPhase.Generating -> "生成 ART+ 草稿"
    WorkPhase.Reviewing -> "逐个审核草稿"
    WorkPhase.Packaging -> "封装已确认图标"
    WorkPhase.ReadyToFlash -> "完成"
    WorkPhase.Failed -> "任务中止"
}


private fun generationStrategyLabel(strategy: GenerationStrategy): String = when (strategy) {
    GenerationStrategy.NativeMonochrome -> "原生 monochrome"
    GenerationStrategy.AospMonochrome -> "AOSP 单色自动生成"
    GenerationStrategy.DarkDominantInvert -> "暗主体亮度反相"
    GenerationStrategy.AdaptiveToneLift -> "Adaptive 提亮"
    GenerationStrategy.LegacyToneLift -> "Legacy 提亮"
    GenerationStrategy.ConservativeFallback -> "保守回退"
}

private fun reviewDecisionLabel(decision: ReviewDecision): String = when (decision) {
    ReviewDecision.Pending -> "待确认"
    ReviewDecision.Approved -> "已通过"
    ReviewDecision.Rejected -> "已拒绝"
}
