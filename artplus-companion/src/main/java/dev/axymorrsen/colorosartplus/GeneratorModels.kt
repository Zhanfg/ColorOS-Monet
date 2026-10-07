package dev.axymorrsen.colorosartplus

import android.graphics.Bitmap
import android.net.Uri

internal enum class WorkPhase {
    Idle,
    RequestingRoot,
    Scanning,
    Generating,
    Reviewing,
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

internal enum class ReviewDecision {
    Pending,
    Approved,
    Rejected,
}

internal enum class GenerationStrategy {
    NativeMonochrome,
    AospMonochrome,
    DarkDominantInvert,
    AdaptiveToneLift,
    LegacyToneLift,
    ConservativeFallback,
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
    val strategy: GenerationStrategy? = null,
    val flipped: Boolean = false,
    val confidence: Float = 1f,
)

internal data class ReviewItem(
    val packageName: String,
    val label: String,
    val original: Bitmap,
    val generated: Bitmap,
    val status: ItemStatus,
    val strategy: GenerationStrategy,
    val flipped: Boolean,
    val confidence: Float,
    val decision: ReviewDecision = ReviewDecision.Pending,
)

internal data class ReviewSummary(
    val pending: Int = 0,
    val approved: Int = 0,
    val rejected: Int = 0,
) {
    val total: Int get() = pending + approved + rejected
}

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
    val reviewItems: List<ReviewItem> = emptyList(),
    val reviewIndex: Int = 0,
    val module: GeneratedModule? = null,
    val managerHandlers: List<String> = emptyList(),
    val logLines: List<String> = emptyList(),
    val error: String? = null,
) {
    val reviewSummary: ReviewSummary
        get() = ReviewSummary(
            pending = reviewItems.count { it.decision == ReviewDecision.Pending },
            approved = reviewItems.count { it.decision == ReviewDecision.Approved },
            rejected = reviewItems.count { it.decision == ReviewDecision.Rejected },
        )

    val currentReview: ReviewItem?
        get() = reviewItems.getOrNull(reviewIndex)
}
