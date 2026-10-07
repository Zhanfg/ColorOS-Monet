package dev.axymorrsen.colorosartplus

import android.graphics.Bitmap
import android.net.Uri

internal enum class WorkPhase {
    Idle,
    RequestingRoot,
    Scanning,
    Generating,
    Packaging,
    ReadyToFlash,
    Failed,
}

internal enum class ItemStatus {
    SystemAdapted,
    ModuleAdapted,
    GeneratedAdaptive,
    GeneratedLegacy,
    ConservativeFallback,
    Failed,
}

internal data class GenerationCounters(
    val total: Int = 0,
    val processed: Int = 0,
    val generated: Int = 0,
    val skippedSystem: Int = 0,
    val skippedModule: Int = 0,
    val conservative: Int = 0,
    val failed: Int = 0,
) {
    val progress: Float
        get() = if (total <= 0) 0f else (processed.toFloat() / total.toFloat()).coerceIn(0f, 1f)
}

internal data class PreviewFrame(
    val packageName: String,
    val label: String,
    val original: Bitmap?,
    val generated: Bitmap?,
    val status: ItemStatus,
)

internal data class GeneratedModule(
    val displayName: String,
    val uri: Uri,
    val generatedPackageCount: Int,
)

internal data class GeneratorUiState(
    val phase: WorkPhase = WorkPhase.Idle,
    val hasRoot: Boolean = false,
    val rootMessage: String = "尚未申请 Root 权限",
    val counters: GenerationCounters = GenerationCounters(),
    val current: PreviewFrame? = null,
    val module: GeneratedModule? = null,
    val managerHandlers: List<String> = emptyList(),
    val logLines: List<String> = emptyList(),
    val error: String? = null,
)
