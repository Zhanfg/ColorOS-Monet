package dev.axymorrsen.colorosartplus

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import java.io.File

internal class GeneratorViewModel(
    application: Application,
) : AndroidViewModel(application) {
    private val _state = MutableStateFlow(GeneratorUiState())
    val state: StateFlow<GeneratorUiState> = _state.asStateFlow()

    private val _installerRequests = MutableSharedFlow<Uri>(extraBufferCapacity = 1)
    val installerRequests: SharedFlow<Uri> = _installerRequests.asSharedFlow()

    private val generatedRoot = File(application.filesDir, "generated-artplus")

    private sealed interface WorkResult {
        val target: IconPipeline.Target

        data class Success(
            override val target: IconPipeline.Target,
            val output: IconPipeline.Output,
        ) : WorkResult

        data class Failure(
            override val target: IconPipeline.Target,
            val error: Throwable,
        ) : WorkResult
    }

    fun startGeneration() {
        if (_state.value.phase in busyPhases) return

        viewModelScope.launch {
            try {
                resetRun()
                updatePhase(WorkPhase.RequestingRoot, "正在申请 Root 权限…")

                if (!RootShell.hasRoot()) {
                    _state.value = _state.value.copy(
                        phase = WorkPhase.Failed,
                        hasRoot = false,
                        rootMessage = "未获得 Root 权限",
                        error = "Root 被拒绝或 su 不可用。",
                    )
                    return@launch
                }

                _state.value = _state.value.copy(
                    hasRoot = true,
                    rootMessage = "Root 已授权",
                )

                updatePhase(WorkPhase.Scanning, "正在扫描系统 ART+ 与现有模块…")
                val adapted = RootShell.scanAdaptedPackages()
                val targets = IconPipeline.launcherTargets(
                    getApplication<Application>().packageManager,
                    getApplication<Application>().packageName,
                )

                var counters = GenerationCounters(total = targets.size)
                _state.value = _state.value.copy(counters = counters)

                appendLog(
                    "扫描完成：桌面应用 ${targets.size} 个；系统已适配 ${adapted.system.size} 个；模块已适配 ${adapted.modules.size} 个",
                )

                updatePhase(WorkPhase.Generating, "开始并发生成草稿…")

                val pending = ArrayList<IconPipeline.Target>(targets.size)
                val reviews = ArrayList<ReviewItem>()

                targets.forEach { target ->
                    when {
                        target.packageName in adapted.system -> {
                            counters = counters.copy(
                                processed = counters.processed + 1,
                                skippedSystem = counters.skippedSystem + 1,
                            )
                            _state.value = _state.value.copy(
                                counters = counters,
                                current = PreviewFrame(
                                    packageName = target.packageName,
                                    label = target.label,
                                    original = null,
                                    generated = null,
                                    status = ItemStatus.SystemAdapted,
                                ),
                            )
                            appendLog("跳过 · 系统已适配 · ${target.label}")
                        }

                        target.packageName in adapted.modules -> {
                            counters = counters.copy(
                                processed = counters.processed + 1,
                                skippedModule = counters.skippedModule + 1,
                            )
                            _state.value = _state.value.copy(
                                counters = counters,
                                current = PreviewFrame(
                                    packageName = target.packageName,
                                    label = target.label,
                                    original = null,
                                    generated = null,
                                    status = ItemStatus.ModuleAdapted,
                                ),
                            )
                            appendLog("跳过 · 已有模块适配 · ${target.label}")
                        }

                        else -> pending += target
                    }
                }

                if (pending.isNotEmpty()) {
                    val workers = chooseWorkerCount(pending.size)
                    _state.value = _state.value.copy(
                        rootMessage = "并发生成草稿 · ${workers} workers",
                    )
                    appendLog("并发生成已启用：${workers} workers")

                    coroutineScope {
                        val input = Channel<IconPipeline.Target>(capacity = workers * 2)
                        val output = Channel<WorkResult>(capacity = workers * 2)

                        val producer = launch {
                            pending.forEach { input.send(it) }
                            input.close()
                        }

                        val workerJobs = List(workers) {
                            launch(Dispatchers.Default) {
                                for (target in input) {
                                    val result = runCatching {
                                        val generated = IconPipeline.generate(target.icon)
                                        IconPipeline.writeAssets(
                                            generated,
                                            File(generatedRoot, target.packageName),
                                        )
                                        WorkResult.Success(target, generated)
                                    }.getOrElse { error ->
                                        WorkResult.Failure(target, error)
                                    }
                                    output.send(result)
                                }
                            }
                        }

                        val closer = launch {
                            workerJobs.joinAll()
                            output.close()
                        }

                        for (result in output) {
                            when (result) {
                                is WorkResult.Success -> {
                                    val generated = result.output
                                    counters = counters.copy(
                                        processed = counters.processed + 1,
                                        generated = counters.generated + 1,
                                        conservative = counters.conservative +
                                            if (generated.conservative) 1 else 0,
                                    )

                                    val status = when {
                                        generated.conservative -> ItemStatus.ConservativeFallback
                                        generated.adaptive -> ItemStatus.GeneratedAdaptive
                                        else -> ItemStatus.GeneratedLegacy
                                    }

                                    val preview = generated.preview()
                                    reviews += ReviewItem(
                                        packageName = result.target.packageName,
                                        label = result.target.label,
                                        original = generated.original,
                                        generated = preview,
                                        status = status,
                                        strategy = generated.strategy,
                                        flipped = generated.flipped,
                                        confidence = generated.confidence,
                                    )

                                    _state.value = _state.value.copy(
                                        counters = counters,
                                        current = PreviewFrame(
                                            packageName = result.target.packageName,
                                            label = result.target.label,
                                            original = generated.original,
                                            generated = preview,
                                            status = status,
                                            strategy = generated.strategy,
                                            flipped = generated.flipped,
                                            confidence = generated.confidence,
                                        ),
                                        reviewItems = reviews.toList(),
                                    )

                                    appendLog(
                                        "草稿 · ${strategyLabel(generated.strategy)} · ${result.target.label}",
                                    )
                                }

                                is WorkResult.Failure -> {
                                    counters = counters.copy(
                                        processed = counters.processed + 1,
                                        failed = counters.failed + 1,
                                    )
                                    _state.value = _state.value.copy(
                                        counters = counters,
                                        current = PreviewFrame(
                                            packageName = result.target.packageName,
                                            label = result.target.label,
                                            original = null,
                                            generated = null,
                                            status = ItemStatus.Failed,
                                        ),
                                    )
                                    appendLog(
                                        "失败 · ${result.target.label} · ${result.error.javaClass.simpleName}",
                                    )
                                }
                            }
                        }

                        producer.join()
                        closer.join()
                    }
                }

                if (reviews.isEmpty()) {
                    _state.value = _state.value.copy(
                        phase = WorkPhase.Idle,
                        rootMessage = "无需生成：未发现需要新适配的图标",
                        reviewItems = emptyList(),
                        reviewIndex = 0,
                    )
                    appendLog("没有新的图标草稿需要审核。")
                    return@launch
                }

                _state.value = _state.value.copy(
                    phase = WorkPhase.Reviewing,
                    rootMessage = "草稿生成完成 · 等待逐个确认",
                    reviewItems = reviews.toList(),
                    reviewIndex = 0,
                    module = null,
                    managerHandlers = emptyList(),
                )
                appendLog("生成完成：${reviews.size} 个草稿，尚未写入任何模块。")
            } catch (t: Throwable) {
                _state.value = _state.value.copy(
                    phase = WorkPhase.Failed,
                    error = t.message ?: t.javaClass.simpleName,
                )
                appendLog("任务失败 · ${t.javaClass.simpleName}: ${t.message.orEmpty()}")
            }
        }
    }

    fun approveCurrent() {
        setCurrentDecision(ReviewDecision.Approved)
    }

    fun rejectCurrent() {
        setCurrentDecision(ReviewDecision.Rejected)
    }

    fun previousReview() {
        val state = _state.value
        if (state.reviewItems.isEmpty()) return
        _state.value = state.copy(
            reviewIndex = (state.reviewIndex - 1).coerceAtLeast(0),
        )
    }

    fun nextReview() {
        val state = _state.value
        if (state.reviewItems.isEmpty()) return
        _state.value = state.copy(
            reviewIndex = (state.reviewIndex + 1).coerceAtMost(state.reviewItems.lastIndex),
        )
    }

    fun exportApproved() {
        val state = _state.value
        if (state.phase != WorkPhase.Reviewing && state.phase != WorkPhase.ReadyToFlash) return

        val approved = state.reviewItems
            .filter { it.decision == ReviewDecision.Approved }
            .map { it.packageName }
            .toSet()

        if (approved.isEmpty()) {
            _state.value = state.copy(
                error = "还没有任何已确认图标。请至少确认一个图标后再导出。",
            )
            return
        }

        viewModelScope.launch {
            try {
                updatePhase(WorkPhase.Packaging, "正在封装 ${approved.size} 个已确认图标…")

                val exported = ModuleExporter.buildAndPublish(
                    context = getApplication(),
                    generatedRoot = generatedRoot,
                    packageNames = approved,
                )

                val module = GeneratedModule(
                    displayName = exported.displayName,
                    uri = exported.uri,
                    generatedPackageCount = approved.size,
                )

                _state.value = _state.value.copy(
                    phase = WorkPhase.ReadyToFlash,
                    module = module,
                    managerHandlers = exported.handlerLabels,
                    rootMessage = "模块已导出 · 尚未刷入",
                    error = null,
                )

                appendLog(
                    "模块已导出：${approved.size} 个已确认图标；不会自动打开 Root 管理器。",
                )
            } catch (t: Throwable) {
                _state.value = _state.value.copy(
                    phase = WorkPhase.Reviewing,
                    error = t.message ?: t.javaClass.simpleName,
                )
                appendLog("导出失败 · ${t.javaClass.simpleName}: ${t.message.orEmpty()}")
            }
        }
    }

    fun recoverLegacyAlpha1() {
        if (_state.value.phase in busyPhases) return

        viewModelScope.launch {
            try {
                _state.value = _state.value.copy(
                    phase = WorkPhase.RequestingRoot,
                    rootMessage = "正在安全恢复 alpha1 残留…",
                    error = null,
                )

                if (!RootShell.hasRoot()) {
                    _state.value = _state.value.copy(
                        phase = WorkPhase.Failed,
                        hasRoot = false,
                        rootMessage = "未获得 Root 权限",
                        error = "Root 被拒绝或 su 不可用。",
                    )
                    return@launch
                }

                val restored = RootShell.restoreLegacyAlpha1Safely()
                _state.value = _state.value.copy(
                    phase = WorkPhase.Idle,
                    hasRoot = true,
                    rootMessage = if (restored > 0) {
                        "恢复完成：已处理 $restored 个旧版图标"
                    } else {
                        "未发现可恢复的 alpha1 备份"
                    },
                    error = null,
                )

                appendLog(
                    if (restored > 0) {
                        "安全恢复完成 · $restored 个应用；如旧模块需要重新挂载，请重启一次"
                    } else {
                        "未发现 alpha1 首次覆盖前备份"
                    },
                )
            } catch (t: Throwable) {
                _state.value = _state.value.copy(
                    phase = WorkPhase.Failed,
                    error = t.message ?: t.javaClass.simpleName,
                    rootMessage = "恢复失败",
                )
                appendLog("恢复失败 · ${t.javaClass.simpleName}: ${t.message.orEmpty()}")
            }
        }
    }

    fun requestInstallerAgain() {
        _state.value.module?.uri?.let { uri ->
            _installerRequests.tryEmit(uri)
        }
    }

    private fun setCurrentDecision(decision: ReviewDecision) {
        val state = _state.value
        val index = state.reviewIndex
        if (index !in state.reviewItems.indices) return

        val updated = state.reviewItems.toMutableList()
        updated[index] = updated[index].copy(decision = decision)

        val nextPending = (index + 1 until updated.size)
            .firstOrNull { updated[it].decision == ReviewDecision.Pending }
            ?: updated.indices.firstOrNull { updated[it].decision == ReviewDecision.Pending }
            ?: index

        _state.value = state.copy(
            phase = WorkPhase.Reviewing,
            reviewItems = updated,
            reviewIndex = nextPending,
            module = null,
            managerHandlers = emptyList(),
            error = null,
        )
    }

    private fun chooseWorkerCount(taskCount: Int): Int {
        if (taskCount <= 1) return taskCount.coerceAtLeast(1)

        val cores = Runtime.getRuntime().availableProcessors().coerceAtLeast(2)
        val maxMemoryMb = Runtime.getRuntime().maxMemory() / (1024L * 1024L)

        val cpuBound = when {
            cores >= 10 -> 6
            cores >= 8 -> 5
            cores >= 6 -> 4
            else -> 2
        }

        val memoryBound = when {
            maxMemoryMb >= 4096 -> 6
            maxMemoryMb >= 2048 -> 5
            maxMemoryMb >= 1024 -> 4
            else -> 2
        }

        return minOf(taskCount, cpuBound, memoryBound, 6).coerceAtLeast(2)
    }

    private fun resetRun() {
        generatedRoot.deleteRecursively()
        generatedRoot.mkdirs()
        _state.value = GeneratorUiState()
    }

    private fun updatePhase(phase: WorkPhase, message: String) {
        _state.value = _state.value.copy(
            phase = phase,
            rootMessage = message,
            error = null,
        )
        appendLog(message)
    }

    private fun appendLog(line: String) {
        val old = _state.value.logLines
        val next = (old + line).takeLast(120)
        _state.value = _state.value.copy(logLines = next)
    }

    private fun strategyLabel(strategy: GenerationStrategy): String = when (strategy) {
        GenerationStrategy.NativeMonochrome -> "原生 monochrome"
        GenerationStrategy.AospMonochrome -> "AOSP mono"
        GenerationStrategy.DarkDominantInvert -> "暗主体自动反相"
        GenerationStrategy.AdaptiveToneLift -> "Adaptive 提亮"
        GenerationStrategy.LegacyToneLift -> "Legacy 提亮"
        GenerationStrategy.ConservativeFallback -> "保守回退"
    }

    private companion object {
        val busyPhases = setOf(
            WorkPhase.RequestingRoot,
            WorkPhase.Scanning,
            WorkPhase.Generating,
            WorkPhase.Packaging,
        )
    }
}
