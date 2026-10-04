# 1. Executive conclusion

[OBSERVED] **COUI 普通 Preference group 是逐行绘制、共同构成连续 grouped card 的模型。** 每行是 RecyclerView item；`COUICardListHelper.getPositionInGroup(Preference)` 根据同一 parent 内的可见相邻项判定 HEAD/MIDDLE/TAIL/FULL，`COUICardListSelectedItemLayout` 只在组边缘画圆角。这里的“整张 card”是视觉分组，不是已证明包住四行的单一 ViewGroup。Confidence: HIGH。

[OBSERVED] **不能声称 ColorOS 17 删除了 `mCardBackgroundColor`。** 输入的 Settings `classes.dex` 明确声明 `COUICardListSelectedItemLayout.mCardBackgroundColor:I`；`COUICustomListSelectedLinearLayout` 继承该类，没有在自身重复声明字段。`refreshCardBg(int)` 写该字段并 invalidate。报告的运行时 NoSuchFieldError 与这份字节码不能直接对齐，实际进程/类加载器/加载版本/异常栈尚缺。Confidence: HIGH（字段存在）；LOW（运行时异常根因）。

[OBSERVED] COE 2.9.3 的 `CardHook` 会重写 native path、组内圆角、间隔、padding 和背景，`ListHook` 会转移 assignment 文本到 summary；两者不是同一种 card 行为。`CardHook.updatePath` 将 native 中间边的零圆角改为默认 4dp，与默认 2dp card gap 组合足以破坏连续分组；这是一条具体静态机制，实际截图的全部因果仍需运行时验证。Confidence: HIGH（机制）；MEDIUM（视觉后果）。

[OBSERVED] 同一 DEX 还含 SettingsLib `SettingsPreferenceGroupAdapter` 的 state_first/middle/last/single drawable 模型，受 `SettingsThemeHelper.isExpressiveTheme(Context)` 控制。它与 COUI path 模型并存，不能用一个全局 CardHook 同时接管。Confidence: HIGH。

[INFERRED] v0.2.0 默认保留上述 native grouping、divider 和 state drawable。当前 **可启用的 segmented-card whitelist 为空**：给定证据不能证明任何具体 screen/key 的 segmented 改造已获完整布局和运行时验证。首页 account/hero 仅是待验证候选，不能自动加入。Confidence: HIGH（准入决定）。

# 2. Observed facts

## 2.1 来源、方法与复现边界

分析分支：`codex/coloros17-hard-analysis-20261004`；冻结实现：`d6206a7885608cc6618f4dc4627c62587f19bd1c`。

私有包 SHA-256：`d23f7b1f2f9489c061c446b912a55e26aab67126f16631c31d4c55a9f7b20501`。合并 001→004 后验证通过；包内 SHA256SUMS 全部通过。

- S：`settings/classes.dex`，SHA-256 `8a43eebe5a3bd9756a624d7649381a8d8a7bba9cd2825d96828095ca8680353b`，解析到 3,663 个 class definitions。
- SR：`settings/settings_resources.filtered.txt`，SHA-256 `35c51b24999269e0e6e9b9c05c570bbddcb5744ba1d9abe513791ec50192c72d`。资源表文本，**不含 layout/drawable XML 内容**。
- C：`coe/COE-2.9.3.apk`，SHA-256 `45cf72d7e872cc11433a5e67a1e3755bac7f779263ef8df511deaec17376e7b7`；以下 COE 证据来自 `classes.dex`。

工具：jadx 1.5.3 辅助阅读；Androguard 4.1.3 独立解析 class/field definitions、继承、invoke 与 field 操作。jadx 存在部分方法恢复错误，尤其 CardHook callback；下列对应机制采用原始指令核对，不能把 jadx 的 UnsupportedOperationException 占位当成 APK 行为。中间源码/指令 dump 仅保留于 `/tmp/coloros17-hard-analysis/`。引用的 PC 是方法内**字节偏移**；code_off 是 DEX 文件偏移。

## 2.2 分组位置与绑定

| Evidence | [OBSERVED] 精确符号及行为 | Confidence |
|---|---|---|
| S-B1 | `COUICardListHelper.getPositionInGroup(Preference):int`：取 `getParent()`，过滤 `isVisible()`，检查前后邻居；无 parent 返回 NONE=0 | HIGH |
| S-B2 | `isSupportCard(PreferenceGroup,Preference):boolean`：parent 为 PreferenceScreen 时邻居须实现 `COUICardSupportInterface` 且 `isSupportCardUse()`；其他 group 排除 PreferenceCategory | HIGH |
| S-B3 | `getPositionInGroup(int count,int index)`：count=1→FULL=4；index=0→HEAD=1；末项→TAIL=3；其余→MIDDLE=2 | HIGH |
| S-B4 | `COUIPreference.onBindViewHolder(PreferenceViewHolder)` PC `0x0a` 调 getPositionInGroup；PC `0x12` 调 `setItemCardBackground(View,int)` | HIGH |
| S-B5 | `COUIListPreference.onBindViewHolder` PC `0x3e/0x46`；`COUISwitchPreference.onBindViewHolder` PC `0x1d8/0x1e0` 也走同一 helper | HIGH |
| S-B6 | `COUICardListHelper.setItemCardBackground` 仅对 `ListSelectedItemLayout` 调 `setPositionInGroup(int)`；非该类不改 | HIGH |
| S-B7 | `COUICardListSelectedItemLayout.setCardRadiusStyle(int)`：HEAD=(top=true,bottom=false)，MIDDLE=(false,false)，TAIL=(false,true)，FULL=(true,true) | HIGH |

算法只基于 Preference hierarchy/可见性/card-support，不能等同于屏幕 RecyclerView child index；滚动回收、隐藏项、PreferenceCategory、父层级会影响两者关系。`getPositionInGroup(Preference)` 本身不检查当前项的 card-support，主要检查邻居。输入为 0 时 `setPositionInGroup` 不更新 path；这不是将旧状态重置成 standalone card 的接口。

## 2.3 背景、形状与状态的独立 owner

| 属性 | [OBSERVED] Owner / method / state | Confidence |
|---|---|---|
| 基础填色 | `COUICardListSelectedItemLayout.init(Context,boolean)` code_off `0x338d9c` 从 `COUIContextUtil.getAttrColor(...couiColorCardBackground)` 初始化 `mCardBackgroundColor:I` | HIGH |
| 填色更新 | `refreshCardBg(int)` code_off `0x338e94` 写字段并 invalidate；匿名 `$1.draw(Canvas)` 用该色 drawColor 或 Paint+drawPath | HIGH |
| 边缘 shape | `setCardRadiusStyle`→`mTopRounded/mBottomRounded`；`updatePath()`→`mCardRect/mPath/mRadii/mRadius/mHorizontalMargin` | HIGH |
| 原生平滑圆角 | `RoundCornerUtil.getSmoothStyleType()`→`COUIShapePath.getRoundRectPath` 或 `OplusPathAdapter.addSmoothRoundRect`；OSVersionCode 分支。保留 branch，不等于普通 addRoundRect | HIGH |
| 圆角参数 | constructor 读 `couiCardRadius`，fallback attr `couiRoundCornerXL`；`getInnerRadius(float)` 的特定版本分支读 `coui_round_corner_xl_radius_normal_16_1` | HIGH |
| 首尾 padding | `setPadding(int)` 使用 `HEAD_OR_TAIL_PADDING`、`mInitPaddingTop/Bottom`、`mMinimumHeight`，可作用于 `mMainLayoutToSetExtraPadding` | HIGH |
| pressed/hover | `ListSelectedItemLayout.initStateEffectBackground()` 创建 `COUIMaskEffectDrawable` + `COUIStateEffectDrawable`；`setBackground(Drawable)` 替换 wrapper 的 view-background 层，保留 wrapper | HIGH |
| 触摸动画 | `dispatchTouchEvent/onTouchEvent`→`handlePressAnimationInternal`→`startAppearAnimation/startDisAppearAnimationOrNot`→`setTouched(boolean)` | HIGH |
| selected | `COUIPreference.mIsSelected` 绑定到 View；`COUICardListSelectedItemLayout.setIsSelected(boolean,boolean)`→`mIsSelected`→state drawable `setStateLocked(1,...)` | HIGH |
| mWithDividerItem | `COUICustomListSelectedLinearLayout.init(Context,AttributeSet)` 读 attr；`onTouchEvent` 为 true 时消费触摸。它**不是 divider painter** | HIGH |

`COUICustomListSelectedLinearLayout` 自有字段为 `mIconMarginDependOnImageView`、`mMarginBetweenLine`、`mTextContentPaddingTop`、`mWithDividerItem` 等布局/触摸信息；基础背景色位于 superclass，交互状态位于 state/mask drawable。不存在“用单个新字段替代所有背景与状态”的证据。

## 2.4 Divider：安装、准入、绘制、动画

[OBSERVED] `com.oplus.settings.SettingsBaseFragment.setPreferenceScreen(PreferenceScreen)` PC `0x1a` 创建 `COUIPreferenceItemDecoration(Context,PreferenceScreen)`，并 addItemDecoration；`onViewCreated` 重新挂接该 decoration。Confidence: HIGH。

[OBSERVED] `COUIPreferenceItemDecoration.shouldDrawDivider(RecyclerView,int)` 查 adapter 的 Preference，调用 `ICOUIDividerDecorationInterface.drawDivider()`；选中项或其邻项会隐藏线，fade-in 时也会隐藏。`COUIPreference.drawDivider()` 要求 `mShowDivider`、card view，并仅 HEAD/MIDDLE 返回 true；TAIL/FULL 不画尾线。start inset 可对齐 `mTitleView`，并支持 RTL。Confidence: HIGH。

[OBSERVED] 真正画线是 superclass `COUIRecyclerView.COUIDividerItemDecoration.onDrawOver(Canvas,RecyclerView,State)`，用 Paint.drawRect 或 drawable.draw，读 `mDividerColor/mDividerStrokeWidth/mPressDividerAlpha`。`COUIRecyclerDividerManager` 用 COUISpringAnimation 管理按压邻近 divider alpha，默认启用 press hide。Confidence: HIGH。不能通过全局透明色代替这种状态语义。

SR 资源名→ID：`attr/couiColorCardBackground=0x7f04028f`；`attr/couiColorDivider=0x7f0402a7`；`attr/couiPreferenceWithDividerItem=0x7f0403ba`；`dimen/coui_list_card_head_or_tail_padding=0x7f07055f`（2dp）；`dimen/coui_list_divider_height=0x7f070564`（0.33dp）；`layout/coui_preference=0x7f0e0198`。Confidence: HIGH（表内记录）；这些数值/ID 限定于 S/SR，不可硬编码到其他包。

## 2.5 第二条 SettingsLib 分组路径及页面边界

[OBSERVED] `SettingsPreferenceGroupAdapter.buildItemPositionStates()` 根据 parent、group-divider、ChainedMixin、Expandable 的展开状态建 `mItemPositionStates:[I`，`closeGroup(int[],int)` 将末端 FIRST 改 SINGLE、MIDDLE 改 LAST。`onBindViewHolder` 先 super（Preference 自身绑定），再在 `SettingsThemeHelper.isExpressiveTheme(Context)` 为 true 时执行 `updateBackground`。DrawableStateLayout 分支使用 `settingslib_round_background_stateful`；其他分支取 round-corner drawable。Confidence: HIGH。

[OBSERVED] `SettingsThemeHelper.isExpressiveTheme` SDK<36 返回 false；其余读 expressive 属性、Activity 的 ExpressiveDesignEnabledProvider 或 Flags。**UXDesign 的 EXPRESSIVE 调色 Variant 与这里的 expressive UI gate 不能合并认定为同一设置。** Confidence: HIGH（独立门控）；UNKNOWN/LOW（当前设备门控值）。

[OBSERVED] `SettingsPreferenceFragment.onCreateAdapter` 返回 `OplusHighlightablePreferenceGroupAdapter`，继承链为该类→`HighlightablePreferenceGroupAdapter`→`SettingsPreferenceGroupAdapter`→`PreferenceGroupAdapter`。`OplusHighlightablePreferenceGroupAdapter.onBindViewHolder` 可调用 `changeDrawCanvasType(true)`，保留 highlight 机制。Confidence: HIGH。

[OBSERVED] `SettingsHomepageActivity` 持有/创建 `TopLevelSettings`；`OplusTopLevelSettings.onCreateRecyclerView` 有 SimpleMode 分支以及缓存/自有 recycler layout 路径。`DeviceInfoFragment.onCreateAdapter` 调父方法并启用 delayed highlight，`onCreateLayoutManager` 创建 GridLayoutManager(2)，已见 span lookup 返回 2。**About Device 不能按普通首页 card 重写。** Confidence: HIGH（静态结构）；MEDIUM（完整屏幕覆盖，缺 XML/runtime）。

## 2.6 COE 破坏分组的具体机制

[OBSERVED] C 的 `HookEntry.installNonSystemUiHooks` 安装 CardHook/ListHook 等；CardHook 自身仅排除 android/SystemUI，存在 enable gate，却没有严格 Fragment/adapter 白名单。首页判断使用 Activity 名 substring 与全局当前首页标志；不是 component identity。Confidence: HIGH。

[OBSERVED] `CardHook$handleLoadPackage$7.afterHookedMethod` code_off `0x2d9ccc`：PC `0x3c6` 字段名 `mCardBackgroundColor`、`0x3ce` getIntField、`0x41e` setIntField；PC `0x61e/0x62a` 写 bottomMargin/topMargin。与 native bind 相互作用，异常可发生在同一 callback 已修改部分状态后。Confidence: HIGH。

[OBSERVED] `$8.afterHookedMethod` hook `COUICardListSelectedItemLayout.updatePath()`，读取 native top/bottom 状态或 additional effective-position，随后 reset path 并 **用 Path.addRoundRect 替换原生 smooth path**。组内边也使用 small_radius，默认 4dp；组边默认 large_radius=20dp，capsule 使用额外 radius。C 的 `yp` 默认 `card_gap=2`、`secondary_top_margin=16`、`extra_padding=4`、`min_height=62`。Confidence: HIGH。

[INFERRED] 这使原本中间相邻行的直边变成小圆角，间隔把逐行背景暴露出来，从而产生“小圆角卡片拼接”的外观；无需假设 native 原先也是 standalone cards。具体页面与截图必须再验证。Confidence: MEDIUM。

[OBSERVED] `ListHook.handleLoadPackage` hook `COUICustomLinearLayoutForPreference.onMeasure(int,int)`；读取 title/summary/assignment、按 flags 将 assignment 移入 summary，改 visibility，并有 StorageDashboardActivity 名称例外。没有 native group-aware screen predicate。它会影响内容和高度，但 **未见该 Hook 本身决定 corner/path**。Confidence: HIGH。不应把 CardHook 的路径重写归因给 ListHook。

[OBSERVED] `remove_card_divider` 的入口属于 `HookEntry.handleInitPackageResources`，不是上述 row painter；需将资源替换与 runtime path/state 独立治理。Confidence: HIGH。

# 3. Runtime flow

以下为 **静态可达链**，不是已经采集到的运行时 trace：

```text
SettingsHomepageActivity / 普通 SettingsPreferenceFragment / DeviceInfoFragment
  → PreferenceScreen + visible Preference hierarchy
  → SettingsPreferenceFragment.onCreateAdapter
  → OplusHighlightablePreferenceGroupAdapter
  → HighlightablePreferenceGroupAdapter
  → SettingsPreferenceGroupAdapter
  → PreferenceGroupAdapter.onBindViewHolder
      → Preference.onBindViewHolder [COUIPreference / COUIListPreference / COUISwitchPreference]
      → COUICardListHelper.getPositionInGroup(Preference)
      → setItemCardBackground(View, HEAD/MIDDLE/TAIL/FULL)
      → ListSelectedItemLayout virtual dispatch
      → COUICardListSelectedItemLayout.setPositionInGroup
          ├ setPadding
          ├ setCardRadiusStyle → top/bottom flags
          └ updatePath → COUIShapePath / OplusPathAdapter
      → SettingsLib expressive-gated updateBackground [second path]

row base color: couiColorCardBackground → mCardBackgroundColor → background drawable
interaction: touch/hover/selected → state wrapper + mask path
separator: SettingsBaseFragment → COUIPreferenceItemDecoration
           → Preference.drawDivider → COUIDividerItemDecoration.onDrawOver
           → COUIRecyclerDividerManager press alpha
```

[INFERRED] 四行组的 COUI 外观为 HEAD(仅上圆角)、MIDDLE(直边)、MIDDLE(直边)、TAIL(仅下圆角)，间内 divider；独项 FULL 上下均圆。RecyclerView 每行独立拥有背景 drawable，而连续视觉由位置、margin 与 decoration 协作完成。Confidence: HIGH（算法结果）；实际布局是否额外外包 container 仍 NEEDS_RESOURCE_XML。

# 4. ColorOS 16 → ColorOS 17 delta

未提供 ColorOS 16 Settings DEX，因此下表 old 列是 **COE 2.9.3 实际假设**，不是已做双版本 native 字节码比较。

| Old assumption | ColorOS 17 reality | Evidence | Migration action |
|---|---|---|---|
| 反射 mCardBackgroundColor 是统一背景契约 | S 的基类仍有 private int；子类继承；pressed/selected 分离到 drawable | S field definitions + init/refreshCardBg + state wrapper | 用已验证 public 方法；禁止猜替代字段 |
| updatePath 可统一换成 addRoundRect | native 有 OPlus smooth-path 分支 | S updatePath；C callback $8 | REMOVE OLD OVERRIDE |
| 所有 preference 行可给小圆角和 gap | native middle 无上下圆角；group-aware divider | S-B1…B7；C callback $7/$8 | REPLACE 为明确 screen/component predicate |
| 标题、assignment、summary 可通用重排 | COUICustom 布局有多行 icon 对齐逻辑；ListHook 在 onMeasure 全面重排 | S custom onMeasure；C ListHook | 默认禁用；仅完整自有布局范围准入 |
| 一个 card hook 负责所有状态 | background/path/divider/mask/highlight 分属不同 owner；还有 SettingsLib gate | S 2.3–2.5 | 保留独立责任 |
| NoSuchFieldError 证明字段全 ROM 被删 | 本输入反证 universal-deletion；实际报错 class provenance 缺失 | S field 与继承表 | NEEDS_RUNTIME_TRACE，fail closed |

# 5. Implication for v0.2.0

| Screen/component | Policy | 可验证边界 / Confidence |
|---|---|---|
| Settings 首页 | KEEP NATIVE 默认；account/hero 仅可候选 MD3E AUGMENT | Activity→TopLevelSettings 已见；具体 key/layout/state NEEDS_RESOURCE_XML / MEDIUM |
| 普通二级设置页 | KEEP NATIVE continuous groups、insets、divider、mask、highlight | COUI preference bind/helper/decoration HIGH；具体页面逐项验收 |
| About Device | DO NOT HOOK 通用 card/list；保留 grid/span/highlight | DeviceInfoFragment+Oplus adapter HIGH |
| Preference dialogs | KEEP NATIVE dialog family；不继承主屏 segmented 政策 | 独立 dialog 类/layout 索引；完整内容 NEEDS_RESOURCE_XML / MEDIUM |
| popup/menu | KEEP NATIVE menu geometry/separators；DO NOT HOOK card path | 没有得到 screen/component consumer 的准入证据 / LOW |
| 搜索结果 | KEEP NATIVE result/highlight；禁止按 title 误认首页项 | 未提供完整搜索渲染链 / LOW |
| account/hero area | 未准入；需 key、view、adapter 与 lifecycle 一致验证 | 当前 COE 仅 Activity/title/string 逻辑不足 / HIGH（拒绝准入） |

REMOVE OLD OVERRIDE：package-wide CardHook/ListHook、global coui_round_corner_*、global divider suppression。MD3E AUGMENT：只有 component 完整识别后才讨论 semantic tint 或 bounded state/motion；不能以 card-support interface 单独判定“应变成 segmented”。

**Segmented-card whitelist：`[]`。** 当前没有可以诚实列为“已验证适合 segmented”并直接启用的 screen/key；下节给候选验证契约，不把未验证候选伪装成白名单。

# 6. Patch contract

候选 source-level 边界（设计契约，不在本分支实现）：

| Target class / method | Guard | Scope | Fallback |
|---|---|---|---|
| `COUIPreference.onBindViewHolder(PreferenceViewHolder)`；必要时分别列 COUIListPreference/COUISwitchPreference 同签名 | exact Activity + active Fragment + adapter + Preference key + concrete itemView；实现 COUICardSupportInterface 且 isSupportCardUse；layout/hash/version 均获准；不是以 title 匹配 | 显式 whitelist tuple 内的单个 component；保留 helper 原始 position | 不准入则完全调用 native |
| `COUICardListSelectedItemLayout.refreshCardBg(int)` | 仅上行 component 已准入，并且 semantics/color consumer 已验证 | base fill；不写 mMaskDrawable/state 或 mPath | 不存在则不开启 augmentation |
| `COUICardListHelper.getPositionInGroup(Preference)` | 仅观测绑定关联，完整 overload 验证 | 保留结果；不得全局改 FULL | 未识别则不参与 |
| `COUIPreferenceItemDecoration.shouldDrawDivider(RecyclerView,int)` | 当前无可启用 override 契约 | DO NOT HOOK；保留 selected/fade/position 语义 | native |
| `COUICustomLinearLayoutForPreference.onMeasure(int,int)` | 当前无 whitelist | DO NOT HOOK 全局 assignment 转移 | native |

短伪代码：

```text
tuple = (exactActivity, activeFragment, adapterClass, preferenceKey, viewClass)
if tuple not in validatedWhitelist: return native
if !cardSupport || !layoutVerified || positionUnknown: return native
if dialogOrPopupOrSearch || classLoaderMismatch: return native
applyOnlyApprovedSemanticAugmentation(tuple)
```

whitelist 目前为空；没有 Fragment provenance 时不能退化成 Activity 或包名判断。保留 switch、可见性变化、item recycling、disabled、selected/highlight 与 light/dark 的验证要求。

# 7. Failure/fallback behavior

[INFERRED] 未命中 class/method/signature、背景不是预期 wrapper、未找到 Preference/Fragment/adapter、资源缺失或加载来源不一致时 **fail closed**，保留 native。安装前整体校验 component 的必需符号；不能先改 margin/path 再发现字段缺失而遗留部分样式。Confidence: HIGH（迁移契约）。

不要在 `mCardBackgroundColor` 查找失败后猜另一个字段；记录一次 tuple/classloader/declaring-class 信息，关闭该 component。不要猜新类名、扩大包范围、清除 divider 或换全局 background 作为 fallback。

# 8. Unknowns

| Required evidence | 具体缺口与影响 | 补充方式 |
|---|---|---|
| NEEDS_RUNTIME_TRACE | NoSuchFieldError 的完整栈、进程/包、View 的 classloader、superclass/declared fields、加载 APK 路径与版本。S 明确有字段，不能证明报错对象就是此版本 | 原机只读记录 constructor/bind 的 class provenance；与 S 哈希匹配；同时记录 Xposed field lookup 的实际调用栈 |
| NEEDS_RESOURCE_XML | Settings APK 的上述 layout/drawable/style XML；filtered resource text 只给 ID/path，不能证明完整 View tree、额外 group container 或 screen→item root | 提供只相关 binary XML 或只读 dump；核对实际 inflate resource 与 theme attrs |
| NEEDS_RUNTIME_TRACE | SettingsLib expressive gate 的当前值、两种背景绑定的最终先后效果、首页/二级/About Device/search/dialog 实际 consumer | 分屏记录 Activity/Fragment/adapter/key/itemView、helper result、background 类型、decoration、gate 值；开关/隐藏/回收/highlight 状态各采样 |
| NEEDS_RAW_BYTECODE | ColorOS 16 对照、异常发生的其他包自己的 COUI DEX；不能将 Settings 的字段契约推广为所有 COUI APK | 提供具体旧版或故障包 DEX，并单独建立 checksum/class matrix |
| NEEDS_RESOURCE_XML | account/hero 的 exact key/layout 与搜索/菜单选择器 | 补充原始相关 XML 后再给 whitelist tuple；不能从名称推定 |

这些缺口不妨碍确认 S 的分组算法和 C 的路径改写；它们阻止宣称运行时全覆盖、解释唯一异常根因，或给出可启用的 segmented whitelist。第一份报告完成的是静态结构基线；没有宣称设备视觉验收已通过。
