# 1. Executive conclusion

[OBSERVED] COE 2.9.3 的风险来自实际 mutation 范围，不能只用类名迁移表解释。CardHook 重写原生路径/行距，ListHook 重组 preference 内容；resource-init 还另行移除 divider。三者必须分拆，取消广泛安装，换为明确 screen/component predicate。提供的 Settings DEX **仍有 mCardBackgroundColor**，因此已报告 NoSuchFieldError 的具体来源未证实，不能编造替代字段。Confidence: HIGH（代码）；LOW（设备异常归因）。

[OBSERVED] MonetColorSpec2025Hook 会在 native createOverlays 期间替换 FabricatedOverlay 的 system_* 值。ColorOS 17 输入中的 native ColorScheme 已显式使用 **SPEC_2026**，MaterialDynamicColors.colorSpec 是 ColorSpec2026。建议 **DELETE** 此全局算法替换；保持 native style/seed/contrast/用户选择。Confidence: HIGH（静态覆盖与native算法）；MEDIUM（启用时运行覆盖规模）。

[OBSERVED] QsLottieHook 的 QSIconViewProxy 目标与 overload **仍存在**；它返回null/清除state强制走drawable，不能写“已迁移到未知plugin类”。AospMediaCardHook 已插件感知，但 root 字符串是旧namespace，并有全局View/ImageView拦截、自造布局/颜色；建议 **REPLACE** 为插件内单组件语义增强，简单RETARGET不能满足native-first。Confidence: HIGH。

下面 action 是 v0.2.0 迁移决定；KEEP 不等于已通过设备兼容测试，NEEDS_EVIDENCE 不授权启用。

# 2. Observed facts

## 2.1 Provenance / reproduction

C：`coe/COE-2.9.3.apk` SHA-256 `45cf72d7e872cc11433a5e67a1e3755bac7f779263ef8df511deaec17376e7b7`（包内实际文件名按输入清单）；两个层面核对：jadx 1.5.3 阅读、Androguard 4.1.3 原始DEX definitions/invokes/field accesses。所有反编译输出保存在仓库外。PC为方法内字节偏移。

S：Settings classes.dex，见02。M/P：SystemUI classes2-monet/classes3-materialsdk/classes4-oplus-components 与 SystemUIPlugin classes.dex；哈希见03。只在这些切片未定义不等于整个ROM不存在；Launcher/Keyguard/系统framework实现不齐。

## 2.2 Dispatcher 与重要 Hook 兼容矩阵

[OBSERVED] `HookEntry.installNonSystemUiHooks` 固定安装Card/List/Overscroll/Switch/Toolbar。`isNonSystemUiApp` 仅排除android、SystemUI、模块进程；不是Settings页面准入。`handleLoadPackage` 的jadx恢复失败，使用raw invoke inventory核对：Monet PC `0x18c/0x192`，QS Lottie `0x31a/0x320`，Media `0x42a/0x444`，VolumeOld `0x2fa/0x300`。也有构造与分支调用差别，不以“APK内有类”代替dispatch证明。Confidence: HIGH。

Old target来自C，并非另行取得的ColorOS16 DEX。Status 描述提供输入与设计匹配情况。矩阵证据标注中的C/M/P/S均为静态观察；决定为[INFERRED]政策。

| Old hook | Old target / mutation | ColorOS 17 target | Status / evidence / confidence | Action |
|---|---|---|---|---|
| CardHook | COUICardListHelper、COUICardListSelectedItemLayout.updatePath；field/margin/path | 同名native helper/base/subclass，见02 | S+C定义与call；field仍存在，package模型不合格；HIGH | REPLACE |
| ListHook | COUICustomLinearLayoutForPreference.onMeasure；assignment→summary | S中同名view与nativebind | C callback不验证fragment/adapter；HIGH | REPLACE |
| MonetColorSpec2025Hook | ThemeOverlayController.createOverlays + FabricatedOverlay.setResourceValue | M同controller，native SPEC_2026 | 真实生成target仍存在；替换parallel算法；HIGH | DELETE |
| QsLottieHook | QSIconViewProxy/Companion.getLottieAnimAsset、setIcon | M classes4 同class/overloads | 仍命中native owner，清除Lottie；HIGH | REPLACE |
| AospMediaCardHook | plugins.shared.view.template.media.MediaPlayerCardPageRootView；View/ImageView全局拦截 | P shared.template.section.media.MediaPlayerCardPageRootView | 旧root未定义、新root定义；已感知plugin但重建native组件；HIGH | REPLACE |
| MediaSeekBarHook | 旧media root、DirectionAwareSeekBar | P新root、同DirectionAwareSeekBar | helper/root predicate需改，不能移植全部动画；HIGH/MEDIUM | RETARGET |
| MediaCreditCleanupHook | LiveAlertTextView +文本匹配隐藏 | P同LiveAlertTextView | class定义不证明特定credit语义；HIGH/LOW | NEEDS_EVIDENCE |
| LockscreenLyricsHook | plugin loader、LyricsRecyclerView/LyricsSwitcherView | P LyricsRecyclerView定义，Switcher未在切片定义 | lifecycle/method/layout未全验证；MEDIUM | NEEDS_EVIDENCE |
| FontHook | OplusQSClock、SimpleQSClock、StatClock/TextView | M SimpleQsClock extends OplusQSClock | 旧SimpleQSClock未定义，新大小写精确不同；全局TextView仍须收窄；HIGH | RETARGET |
| QsDrawableHook | QSDrawableBuilder/Gradient/MixColor builder + fake refresh | M同builder家族/部分匿名class不同 | nativeflow被重发与drawable替换；HIGH/MEDIUM | REPLACE |
| ClassicQsHook | OplusQSHighlightTileViewImpl/OplusToggleSliderView | M同类 | 重设QS视觉与native-preservation冲突；HIGH | DELETE |
| QsHighlightCornerHook | plugin resizeable tiles + Gradient/MixColor/TileDrawableWrapper | M classes4同时包含plugins.qs resizeable tiles及drawables | namespace含plugins不证明独立loader；固定corner重写；HIGH | DELETE |
| QsHighlightCornerHookOld | OplusQSResizeableTileViewTwoXOne/OplusQSIconView | M classes4同类 | 与新版corner路径重复且仍替换几何；HIGH | DELETE |
| QsThreeStageCornerHook | OplusQSThreeStageLayout/RoundRectOutlineProvider | M classes4 layout及outline | 原生stage geometry应保留；HIGH | DELETE |
| QsVerticalSliderHook | COUIVerticalSeekBar/OplusQsBaseToggleSliderLayout | M classes4 base seek及plugins.qs OplusQsToggleSliderLayout | 独立运行loader仍需trace，保留native滑块分工；HIGH | REPLACE |
| StockVolumeDialogHook | AOSP VolumeDialogImpl/内部类；OplusVolumeModule.provideVolumeDialog | M OplusVolumeDialogImpl→OplusVolumeDialogView；provider未给 | C试图选择/修补AOSP；M OPlus组件链存在，DI选择未给；HIGH/MEDIUM | DELETE |
| VolumeDialogHook | OplusVolumeDialogImpl、View、SeekBar、anim utils | M同家族 | 存在不等于替换动画/形状兼容；未来仅semantic consumer；HIGH/MEDIUM | REPLACE |
| VolumeDialogOldHook | OplusVolumeDialogImpl、OplusVolumeRow、COUIVerticalSeekBar | M同家族 | dispatcher明确安装；旧固定corner/动画scope不合格；HIGH | REPLACE |
| NotificationHook / ColorOSNotifyIconPatch | row/background/outline/stack/extensions | M base row + OPlus extensions，见03 | 大量target仍存在，跨通知状态重写需拆分；HIGH/MEDIUM | REPLACE |
| ScrimHook | android SystemUI ScrimView | M ScrimView | shade面层不能作为每组件颜色/blur总owner；HIGH | DELETE |
| ScrimAltHook | ScrimControllerExImp/BlurMixConfig/MixColor | M同类 | 全局混色覆盖不能替代原生blur分工；HIGH | DELETE |
| ShadeHeaderForegroundHook | QsColorUtil/OplusQuickStatusBarHeader/fakeviews | M同家族 | 假视图/主题/深浅状态仍需绑定trace；MEDIUM | NEEDS_EVIDENCE |
| CapsuleNotificationTextColorHook | CapsuleNotificationDataController、LiveAlertTextView | M controller、P view | capsule/plugin状态角色需完整consumer验证；MEDIUM | NEEDS_EVIDENCE |
| PanoramicAodCapsuleBackgroundHook | CapsuleBackgroundView/CapsuleEarView/ScrimControllerEx | M同类 | AOD/锁屏不在已验证semantic scope；MEDIUM | NEEDS_EVIDENCE |
| PixelLockscreenClockHook | Keyguard root/资源/动态classloader | keyguard slice不全；M SchemeClock != view root | Pixel替代设计不属于本项目native-first scope；HIGH政策 | DELETE |
| GestureHook | SideGestureDetector/GesturePointContainer | M同家族 | navigation行为应保持native；HIGH政策 | DELETE |
| StockUdfpsIconHook | OnScreenFingerprintUiMech、AOD/ripple | M部分定义，framework/auth部分未给 | 保留native artwork目标正确，具体Hook兼容未验证；MEDIUM | NEEDS_EVIDENCE |
| BatteryPercentTextSizeHook | resource-init battery percent dimens | M battery view定义、只有筛选资源text | 文字/资源位置与scale需consumer/XML验证；MEDIUM | NEEDS_EVIDENCE |
| NativeGlobalActionsLiteHook | GlobalActionsDialogLite/系统服务/资源 | 切片/依赖不齐 | 保留native power menu，暂不授权替换；LOW | NEEDS_EVIDENCE |
| OverscrollHook | COUIRecyclerView/PercentWidthRecyclerView/OplusRecyclerView | S COUIRecyclerView family | 原生overscroll/motion不能全应用覆盖；HIGH政策 | DELETE |
| SwitchHook | COUISwitch及legacy OPlus class | S/M COUISwitch | 本地view存在；touch/state/row双路径须component收窄；HIGH/MEDIUM | REPLACE |
| ToolbarHook / CouiToolbarHookFade / ToolbarHookScale | AppBar/toolbar/SearchViewAnimate | S AppBarBlurHelper/ToolbarMaterialEffectDelegate | blur/native motion应保留，不继承全局变换；HIGH/MEDIUM | DELETE |
| PopupHook | COUITouchListView.canSelect/StatefulDrawable touch | S/M poplist/state family | 不是grouped-card；nativepopup状态不应全局移除；HIGH | DELETE |
| SettingsThemeUtilsHook | ThemeUtils.isRejectTheme + COUIThemeOverlay.isRejectTheme | S/M COUIThemeOverlay；具体Settings helper待核对 | C强制返回true，改变主题门控；HIGH | DELETE |
| AppInfoButtonHook | COUIButton onMeasure/layout/touch | S COUIButton；页面映射未完 | 限AppInfo页按钮尚需layout/runtime身份；MEDIUM | NEEDS_EVIDENCE |
| WifiButtonHook | WifiOperateItemView | 无WirelessSettings DEX | 请求缺字节码，不凭resource存在启用；LOW | NEEDS_EVIDENCE |
| IconMaskOverlayHook | SystemServer/FRRO adaptive-icon-mask | 无framework/services完整DEX | 不得替换native icon artwork/mask；HIGH政策 | DELETE |
| DockHook / DockHookExp | OplusHotseat/DeviceProfile/CellLayout | 无Launcher DEX | v0.2.0系统scope不授权Launcher视觉重写；HIGH政策 | DELETE |
| MaterialHook / RecentsStyleHook | Launcher decoration/press/recents | 无Launcher DEX | 触及native geometry/motion且scope外；HIGH政策 | DELETE |
| FolderIconBlurMixHook / LauncherScrimSuppression | FolderIcon/PreviewBackground/blur | 无Launcher DEX | 本次无法验运行兼容；native保留，不纳入v0.2.0；LOW | NEEDS_EVIDENCE |
| ThemedIconHook | LauncherIconConfig/UxIconLoaderUtil/WorkspaceItemInfo | UXDesign icon生成有证据，Launcherconsumer无DEX | 不能用UXDesign存在证明Launcher Hook；LOW | NEEDS_EVIDENCE |
| ModuleStatusHook | module内部状态接口 | 模块自身 | 可保留诊断，不承担vendor视觉；HIGH | KEEP |

## 2.3 三个核心 Hook 的实际机制

[OBSERVED] Card/List的callback、默认值、field/path/divider分工见02 §2.6。`mCardBackgroundColor` 在S base class仍为private int，子类继承；读取失败不证明ROM17统一删除。需记录actual process/classloader/declaring class/hash，再决定access兼容。**不能用捕获异常后继续改margin/path作为fallback。** Confidence: HIGH。

[OBSERVED] Monet `installGenerationHook(Class)` code_off `0x28d644` PC `0x0a` 字符串createOverlays；`installOverlayValueHook` code_off `0x28d6d0` PC `0x0a` 字符串setResourceValue，均hookAllMethods。before读seed/style/contrast，建COE自有scheme，ThreadLocal传给资源写入callback；resource callback替换args[2]，after清ThreadLocal。其177是COE EXPECTED_RESOURCE_COUNT，**未证明是native当前完整resource数量**。Confidence: HIGH。

[OBSERVED] `readThemeStyle` code_off `0x28c9d4` PC `0xfc` 明确“mThemeStyle unavailable; using TONAL_SPOT”。native字段现在int，COE支持Number但自有STYLE_NAMES固定0..9；nativeColorScheme支持0..10且SPEC_2026。失败时猜TONAL_SPOT不是fail closed。Native还含CustomDynamicColors、OPlus neutral2_900特例；COE自己的map不能视为等价native。Confidence: HIGH。

[OBSERVED] QS native classes4 `QSIconViewProxy` 持有context/iconHostView/QSLottieAnimationView/state/lottiePrefix/tintList；Companion两个getLottieAnimAsset overload依state与lottieSupport bits选择asset；`setIcon(State,boolean)`存在，jadx失败处用raw invoke核对。C `shouldUseLegacyDrawablePath` code_off `0x2badd0` 只按prefix starts qs_ / contains _lottie决定；有isGlobalThemeApplied helper不代表最终predicate调用它。它抑制native动画，不是找到了新MD3E动画owner。Confidence: HIGH。

[OBSERVED] media hook有OPlusPluginClassLoader constructor/loadClass监听，说明已识别plugin boundary；但是旧ROOT_CLASS没有在P定义，新root只有FrameLayout lifecycle/measure，无background fields。全局View.setAlpha/setVisibility、ViewGroup.dispatchTouchEvent、ImageView.setImageDrawable callbacks +自建ripple/palette越过root自身职责。目标名字改对不足以修好。Confidence: HIGH。

# 3. Runtime flow

以下为静态路径；设备启用情况需要trace：

```text
HookEntry.handleLoadPackage + config
  ├ broad non-SystemUI → CardHook(path/margins) + ListHook(content) + shared widget hooks
  ├ SystemUI → MonetColorSpec2025Hook
  │    native createOverlays(seed)
  │      → COE ThreadLocal own scheme
  │      → native FabricatedOverlay.setResourceValue → COE replaces value
  │      → native transaction.commit (COE colors, native controller metadata)
  ├ SystemUI → QsLottieHook → QSIconViewProxy → null asset / cleared lottie state
  └ plugin classloader → old media root predicate + broad framework-view callbacks

Replacement direction:
 verified Activity/Fragment + Adapter + bound View + role + native update generation
  → one component semantic augmentation
  → retain native group/path/divider/motion/artwork
```

[INFERRED] Monet替换会令native controller持有的ColorScheme与已写resource不同；native的“资源是否相同”检查也可受影响。是否反复生成必须运行验证，不能宣称已观测循环。Confidence: MEDIUM。

# 4. ColorOS 16 → ColorOS 17 delta

| Old assumption | ColorOS 17 reality | Evidence | Migration action |
|---|---|---|---|
| mCardBackgroundColor消失、换field即可 | S field仍存在，实际异常的加载实例不明 | 02 rawdefinition + C reflection | REPLACE package hook；先诊断actualclass |
| SimpleQSClock可继续使用 | SimpleQsClock大小写、继承链变为已验证目标 | M classdefinition + C FontHook | RETARGET精确类；核对继承method |
| Monet需2025生成补丁 | native SPEC_2026 + semantic/fixed/custom FRRO | M ctor/controller + C interception | DELETE generation replacement |
| QS Lottie目标已经搬家 | 同QSIconViewProxy overload在M；M classes4另有plugins.qs命名的QS组件 | M defs/caller，Cpredicate | REPLACE suppressor；无证据不retarget |
| AospMediaCardHook是纯AOSP | 早已有plugin watcher，但旧namespace和重建模型 | C constants/callback、P新root | REPLACE |
| AOSP VolumeDialogImpl是主panel | OplusVolumeDialogImpl→OplusVolumeDialogView；当前DI选择需trace | M UI调用链，见03 | DELETE AOSP selector；component native增强 |

# 5. Implication for v0.2.0

KEEP NATIVE：COUI position/path/divider/state、SystemUI生成palette、QS drawable/asset调度、plugin media artwork/geometry、OPlus volume架构、blur与native motion。

REMOVE OLD OVERRIDE：Monet全局重算、Card/List广泛转换、divider透明替换、全局corner与scrim、Pixel lockscreen/Launcher重写。MD3E AUGMENT仅在已验证consumer处用native当前palette的semantic角色。HOOK HERE的候选不等于whitelist准入；DO NOT HOOK未知/缺完整tuple的组件。

[INFERRED] 最小source-level迁移顺序：

1. dispatcher引入feature contract registry；独立移除global resource/algorithm/path操作，保留诊断。
2. Card/List改为component predicate；默认whitelist=[]，先验证单个完整screen tuple。内容重排与颜色角色是两个feature。
3. 删除Monet替代engine和boot强制style；使用native用户更新结果。
4. plugin hook从实际加载class object/loader解析新root与binder；取消全局framework-view hooks，再做media语义角色。
5. Font大小写与MediaSeekBar root只作精确target迁移，method签名/语义仍通过门控。
6. Volume/QS/Notification分别建立contract；不得复制旧resource值/geometry；按03证据关闭未准入功能。

Confidence: HIGH（迁移政策）。binary return-void不作为最终实现，也不在本分支修改APK或shipping代码。

# 6. Patch contract

| Target class / method | Guard | Scope | Fallback |
|---|---|---|---|
| COUICardListHelper.getPositionInGroup(Preference) | S hash、nativeinterface、准确screen/adapter/Preference key | 诊断；不改nativeposition返回 | 不安装 |
| COUICardListSelectedItemLayout.refreshCardBg(int) | 02 whitelist tuple+native generation+confirmedsemantic consumer | 未来单view色；不改path/margin/divider | 完全native |
| COUICustomLinearLayoutForPreference.onMeasure(int,int) | 精确screen/key且确认assignment accessibility语义 | 当前DO NOT HOOK重排；必要功能另立contract | native内容 |
| ThemeOverlayController.createOverlays(int) | 仅诊断event、无return/argument修改 | DO NOT HOOK算法替换；不能以猜style fallback | nativeFRRO |
| QSIconViewProxy.setIcon(QSTile.State,boolean) / Companion.getLottieAnimAsset | 精确tileSpec+nativeasset、loader、overload、用户显式启用、trace通过 | 默认保留所有nativeanimation；未来观测state，不能改QSTile全局共享对象 | 原始asset/state |
| P MediaPlayerCardPageRootView.onAttachedToWindow() | 从实际pluginloader获取；root+component binder+role全验证 | 生命周期诊断；不在root重建surface | 原始plugin |
| SimpleQsClock（继承OplusQSClock的方法） | 定义/继承method解析验证；特定QS clock instance | RETARGET候选，尚不批准globalTextView.setTypeface | native字体 |
| OplusVolumeDialogImpl.onThemeChanged()/onStateChangedH(State) | 03组件契约；不改controller音量/拓扑 | 诊断native更新；semanticconsumer另立contract | nativepanel |

Derived predicate（不是厂商源码）：

```text
allow = contract.enabled && verifiedInputVersion
        && (activity, fragment, adapter, viewClass, preferenceKey) in whitelist
        && nativeCardSupport && bindingPositionKnown && roleConfirmed
        && sameActualClassLoader && nativeUpdateGenerationKnown
if !allow: return without mutation
prepare: resolve all fields/methods/resources before installing any mutation
apply: only approved semantic property to this bound component
on recycle / native theme update: discard stale module state
```

当前Settings segmented whitelist为空。package名称只定位进程，不能充当allow条件。

# 7. Failure/fallback behavior

[INFERRED] 任一target/overload/field/interface/resource/loader不匹配，整个feature关闭；一条去重诊断含hash、实际class、失败contract，禁止猜类名、旧enum索引或默认TONAL_SPOT继续变色。先验证完整契约再安装，避免一半margin已经改、另一半field失败。Confidence: HIGH。

Plugin卸载/reload则解绑并重验证新loader；不持有跨loader的View/class。native主题更新优先，模块不在reboot重写主题JSON；不吞掉原生音量/通知交互异常。未提供COE source仓库，因此本报告是source-level迁移规格，APK派生分析不能假称已交付可维护source patch。

# 8. Unknowns

| Required evidence | 缺口 / 原因 | 最小补充 |
|---|---|---|
| NEEDS_RUNTIME_TRACE | NoSuchFieldError实际thrower/process/loader/hash；S字段与用户报告冲突 | 完整exception stack、target getDeclaredFields及superchain、APK版本/hash；无须上传全ROM |
| NEEDS_RAW_BYTECODE | android.content.theming.ThemeStyle parser、framework blur/services/OplusVolumeModule的DI选择/Launcher/部分Keyguard缺失 | 按矩阵target补对应class DEX；缺失feature保持关闭 |
| NEEDS_RUNTIME_TRACE | 实际COE配置与启用dispatch、反射签名resolve、177 replacement次数与native再生成 | 每feature日志/contract hit，native对照，不把class存在当执行 |
| NEEDS_RESOURCE_XML | 每screen/component layout/style与semantic资源引用 | 有限目标XML/当前resolvedattrs；定位准确root/role |
| NEEDS_RUNTIME_TRACE | pluginreload、tile/notification状态、mediaartwork、volume交互与字体继承方法生命周期 | 原生截图+View/adapter绑定+主题状态/无障碍trace，准入前逐组件采样 |
