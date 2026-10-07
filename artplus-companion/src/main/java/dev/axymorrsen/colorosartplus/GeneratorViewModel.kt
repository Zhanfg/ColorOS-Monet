package dev.axymorrsen.colorosartplus

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
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

    fun startGeneration() {
        if (_state.value.phase in setOf(
                WorkPhase.RequestingRoot,
                WorkPhase.Scanning,
                WorkPhase.Generating,
                WorkPhase.Packaging,
            )
        ) {
            return
        }

        viewModelScope.launch {
            try {
                resetRun()
                updatePhase(WorkPhase.RequestingRoot, "正在申请 Root 权限…")

                val root = RootShell.hasRoot()
                if (!root) {
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

                updatePhase(WorkPhase.Generating, "开始生成缺失图标…")

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

                        else -> {
                            runCatching {
                                val output = IconPipeline.generate(target.icon)
                                IconPipeline.writeAssets(
                                    output,
                                    File(generatedRoot, target.packageName),
                                )

                                counters = counters.copy(
                                    processed = counters.processed + 1,
                                    generated = counters.generated + 1,
                                    conservative = counters.conservative + if (output.conservative) 1 else 0,
                                )
                                val status = when {
                                    output.conservative -> ItemStatus.ConservativeFallback
                                    output.adaptive -> ItemStatus.GeneratedAdaptive
                                    else -> ItemStatus.GeneratedLegacy
                                }
                                _state.value = _state.value.copy(
                                    counters = counters,
                                    current = PreviewFrame(
                                        packageName = target.packageName,
                                        label = target.label,
                                        original = output.original,
                                        generated = output.preview(),
                                        status = status,
                                    ),
                                )
                                appendLog(
                                    when (status) {
                                        ItemStatus.GeneratedAdaptive -> "生成 · 原生分层 · ${target.label}"
                                        ItemStatus.GeneratedLegacy -> "生成 · 智能拆层 · ${target.label}"
                                        ItemStatus.ConservativeFallback -> "生成 · 保守回退 · ${target.label}"
                                        else -> "生成 · ${target.label}"
                                    },
                                )
                            }.onFailure { error ->
                                counters = counters.copy(
                                    processed = counters.processed + 1,
                                    failed = counters.failed + 1,
                                )
                                _state.value = _state.value.copy(
                                    counters = counters,
                                    current = PreviewFrame(
                                        packageName = target.packageName,
                                        label = target.label,
                                        original = null,
                                        generated = null,
                                        status = ItemStatus.Failed,
                                    ),
                                )
                                appendLog("失败 · ${target.label} · ${error.javaClass.simpleName}")
                            }
                        }
                    }
                }

                if (counters.generated == 0) {
                    _state.value = _state.value.copy(
                        phase = WorkPhase.ReadyToFlash,
                        rootMessage = "无需生成：所有可识别应用均已有适配",
                    )
                    appendLog("没有生成新的图标，因此不会创建空模块。")
                    return@launch
                }

                updatePhase(WorkPhase.Packaging, "正在封装可刷入模块…")
                val exported = ModuleExporter.buildAndPublish(
                    context = getApplication(),
                    generatedRoot = generatedRoot,
                )
                val module = GeneratedModule(
                    displayName = exported.displayName,
                    uri = exported.uri,
                    generatedPackageCount = counters.generated,
                )
                _state.value = _state.value.copy(
                    phase = WorkPhase.ReadyToFlash,
                    module = module,
                    managerHandlers = exported.handlerLabels,
                    rootMessage = "模块已生成，准备交给 Root 管理器",
                )
                appendLog("模块已保存到 Download/ColorOS-ARTPlus-Auto/${exported.displayName}")

                _installerRequests.emit(exported.uri)
            } catch (t: Throwable) {
                _state.value = _state.value.copy(
                    phase = WorkPhase.Failed,
                    error = t.message ?: t.javaClass.simpleName,
                )
                appendLog("任务失败 · ${t.javaClass.simpleName}: ${t.message.orEmpty()}")
            }
        }
    }


    fun recoverLegacyAlpha1() {
        if (_state.value.phase in setOf(
                WorkPhase.RequestingRoot,
                WorkPhase.Scanning,
                WorkPhase.Generating,
                WorkPhase.Packaging,
            )
        ) {
            return
        }

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
}
