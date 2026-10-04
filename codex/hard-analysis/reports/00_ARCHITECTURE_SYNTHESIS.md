# 1. Executive conclusion

[OBSERVED] 四份报告已按 **Settings→UXDesign→COE→SystemUI** 顺序完成独立静态分析。冻结实现为 `d6206a7885608cc6618f4dc4627c62587f19bd1c`；工作分支仅 `codex/coloros17-hard-analysis-20261004`。本次只交付报告/derived metadata，不修改shipping implementation，不将任何私有二进制/源码dump提交。Confidence: HIGH。

[OBSERVED] 可靠基线是：Settings存在原生连续group与独立state/divider；UXDesign拥有主题UI、选择状态、候选palette与COUI XML写端；SystemUI拥有Android公共palette与三FRRO的生成/事务；通知、QS、Media、Volume、Clock各有自己的消费者与渲染边界。**“EXPRESSIVE”调色算法与Settings expressive UI gate是不同状态。** Confidence: HIGH（静态结构）。

[OBSERVED] 两个必须纠正的既有假设：提供的Settings DEX **没有删除 mCardBackgroundColor**；native SystemUI **已显式选择SPEC_2026**。不能将运行时错误泛化为全ROM字段删除，也不能用COE 2025 parallel engine替代原生生成。Confidence: HIGH。

[INFERRED] v0.2.0必须形成如下责任栈，组件native color分支也保留：

```text
ColorOS 17 native component structure
        ↓
ColorOS UXDesign / native Monet palette + native component color sources
        ↓
small semantic MD3E resource layer
        ↓
component-scoped COE hooks
```

Confidence: HIGH（证据约束的架构决定）。明确拒绝global COUI round-corner replacement、global divider removal、global card conversion、package-wide CardHook、package-wide ListHook。

[UNKNOWN] 这是静态技术基线，**没有完成设备运行验收**。缺少runtime trace、部分XML/framework/helper definitions时，不能给出可启用的segmented whitelist或已可发布的新RRO列表。所有18项问题均给出当前答案/限制，缺口不是用猜测填充的“完成”。Confidence: LOW（未验证运行部分）。

# 2. Observed facts

## 2.1 Reports / evidence provenance

- [02 Settings grouped-card](02_SETTINGS_GROUPED_CARD_MODEL.md)：Preference→adapter→row→position/path/state/divider；字段反证与screen policy。
- [01 UXDesign Monet](01_UXDESIGN_MONET_PIPELINE.md)：wallpaper/seed/style两套精确分派、XML/secure/configuration、SystemUI FRRO尾链与ownership。
- [04 COE migration](04_COE_293_ANDROID17_MIGRATION.md)：dispatcher/reflection/palette replacement、重要Hook兼容矩阵与source-level计划。
- [03 SystemUI components](03_SYSTEMUI_COMPONENT_MAP.md)：QS/Notification/Media/Volume/Clock五组件与实际blur API。
- [STRUCTURAL_RELATIONS.tsv](STRUCTURAL_RELATIONS.tsv)：选定method的derived调用/field关系，含DEX alias、method descriptor、PC字节偏移、target symbol；**不是完整call graph，也不是runtime trace**。不含指令/register/body/资源数据。

[OBSERVED] 四份输入按001→004合并为ZIP，SHA-256验证 `d23f7b1f2f9489c061c446b912a55e26aab67126f16631c31d4c55a9f7b20501`；包内12个SHA256SUMS项全部通过。APK/DEX/resource各自哈希在对应报告。私有材料及中间文件位于 `/tmp/coloros17-hard-analysis/`，仓库只保留派生文本。Confidence: HIGH。

关系表alias：S Settings classes.dex；U1/U2 UXDesign APK的classes.dex/classes2.dex；C COE APK classes.dex；M2/M3/M4对应SystemUI输入DEX；P对应plugin classes.dex。代码偏移仅适用已记录哈希版本。

复现程序（在公开仓库外执行，需合法持有同一输入）：

1. 顺序合并分片→sha256sum→解包→包内sha256sum -c；不把文件放进repo。
2. jadx 1.5.3读目标class；Androguard 4.1.3直接读DEX class/super/interfaces/field/method descriptor及code item。
3. 根据关系表from_method定位invoke或field操作，核对PC字节偏移；switch需读取payload targets，不能只看case名称。
4. 对严重jadx失败的方法检查raw bytecode；`UnsupportedOperationException(Method not decompiled)`是工具占位，不是厂商行为。
5. 资源ID只在同artifact资源表映射；filteredtext没有XML内容。跨进程/loader/Androidframework引用另列证据缺口。

Confidence: HIGH（复现契约）；这不代替device trace。

## 2.2 Visual ownership map

| Visual property | [OBSERVED] Producer / state / consumer | Confidence |
|---|---|---|
| Settings grouped edges | COUICardListHelper→row position→top/bottom flags→smoothpath；SettingsLib另有expressive-gatedbackground | HIGH / 02 |
| Settings base/state/divider | base field/refreshCardBg；state+mask drawable；decoration+Preference drawDivider+press alpha，三种独立owner | HIGH / 02 |
| native palette/FRRO | UXDesign选择/secure状态→SystemUI ColorScheme/DynamicColors→ThemeOverlayApplier transaction | HIGH / 01 |
| QS tile/icon/press | repositories/interactors/pools→drawable+outline/iconstate；QSIconViewProxy→Lottie/drawable；COUIpresshelper | HIGH / 03 |
| notification | base row/group/outline；OPlus background/ext/blur/material manager；icon original/grayscale/notificationstate | HIGH / 03 |
| template media | P pager/adapter/section→surface/artwork/control/immersive renderers；host数据边界另保留 | HIGH / 03；当前root MEDIUM/LOW |
| OPlus volume | controller→view/adapter/row→seekbar material host；nativecapability/session/animations | HIGH / 03；DI与新helper LOW |
| clock view | DarkIconDispatcher→Clock/OplusQSClock/SimpleQsClock；algorithm SchemeClock不等于View | HIGH / 03 |
| blur/alpha | component capability/state→ViewBlurProxy/motion/platform，P RenderEffect背景/内容；不是通用color/dimen | HIGH / 03 |

## 2.3 Monet ownership map

| Responsibility | Owner / evidence | Rule |
|---|---|---|
| 主题选择 | UXDesign Activity/ViewModel/ColorConfig→SystemColorApplyUtil | 用户拥有选择；module默认不拥有style |
| 预览palette | UxColorManager→ra.m→Google Variant方案 | 保留seed scoring/nativecontrast |
| 公共Android palette | ThemeOverlayController→ColorScheme SPEC_2026→DynamicColors/MaterialDynamicColors/CustomDynamicColors | 禁止COE parallel engine |
| 注册/激活 | ThemeOverlayApplier→OverlayManagerTransaction register/setEnabled/commit | 保留user/profile策略；成功需trace |
| COUI XML生产 | UXDesign ta.f/ta.a/common.u；SystemUIEx可经provider回调UXDesign | 不把online download视为EXPRESSIVE算法输出 |
| 单色icon palette | db.h→z7.b→a8.b→MaterialStyle/OPlus utilities Variant | 与Android style string不是已证实统一表 |
| consumer-local色 | Notification CONTENT、QSglobaltheme/two-tone、media artwork/model、volume本地resources | 保留原生差异，不能统一外推 |

[OBSERVED] A5为 **PARTIAL**：secure observer确会重算Android FRRO，但单字段style写入不等同于ColorOS完整apply，不证明更新所有COUI/XML/icon/组件色。Android ThemeStyle.valueOf完整parser还缺，ID3→EXPRESSIVE算法已实证。Confidence: HIGH（observer/ID）；MEDIUM（实际作用范围）。

## 2.4 Settings ownership map / whitelist

[OBSERVED] 普通group的continuous card由每行背景共同绘制；first/middle/last/single由Preference parent可见相邻card-support关系判定，不由RecyclerView child index或module标题判断。Divider由COUIPreferenceItemDecoration准入、COUIRecyclerView decoration画、manager处理press alpha。Confidence: HIGH。

[INFERRED] 首页、普通二级、AboutDevice、dialog、popup、search、account/hero必须保持各自policy。只有已验证Activity/Fragment/Adapter/Preference key/View/layout/role完整tuple可进入白名单；当前 **segmented whitelist=[]**。接口存在不授权将nativecontinuousgroup拆成segmented。Confidence: HIGH（决定）。

## 2.5 SystemUI / plugin ownership map

[OBSERVED] 按实际DEX划边界：M4中1,081个plugins.qs prefix类，不在P定义；P媒体template的b1 inflate media_card_section→c1→s1证明了绑定consumer。root的新namespace已经确认，但实际XML class引用仍缺。Volume OPlus实现已证明，DI提供者未提供。Confidence: HIGH（静态）；LOW（activeinstance/loader）。

[INFERRED] 五组件分feature维护，无共享CardHook或单一color/blur/shape/motion开关；禁止把plugin class仅通过SystemUI默认loader解析。Confidence: HIGH（契约）。

## 2.6 COE responsibility map / RRO boundary

| Mechanism | v0.2.0 responsibility | Explicit exclusion |
|---|---|---|
| native system services | 生成/激活palette，主题变化，native资源/组件刷新 | module不代管theme_style/FRRO算法 |
| semantic RRO | 经consumer+alias+overlayability验证的单一语义resource，跟随native当前system_*；不嵌自造palette | geometry/background/divider/disabled/press/alpha/blur/vendorartwork全局覆盖 |
| scoped runtime Hook | 活跃组件的已证实state/semanticconsumer，按tuple+loader+version+generation；回收/主题变化清理 | globalView/TextView hooks、package转换、猜class fallback |
| diagnostics | contract命中/缺符号/实际loader与generation，只读、不记录用户通知内容 | 不能用诊断hook顺便强制style或另生成palette |

[INFERRED] 04矩阵中的DELETE/REPLACE/RETARGET优先落实；KEEP仅模块诊断接口。NEEDS_EVIDENCE条目不可随兼容版本号直接启用。Confidence: HIGH。

# 3. Runtime flow

静态责任图，`?`表示缺证；不会将这张图当已采集现场trace：

```text
USER NATIVE THEME ACTION
  → UXDesign ColorConfig / Google-style UI selection
  → secure JSON + OPlus configuration / provider/XML branches
  → SystemUI secure observer / wallpaper + contrast callbacks
  → ThemeOverlayController → ColorScheme(SPEC_2026)
  → semantic/fixed/custom roles → three FabricatedOverlay → transaction.commit
  → Android system_* resources
  → ? selected component resource alias
  → component native state/render consumer
  → [future] approved tiny semantic RRO / one bound COE augmentation

COUI resource branch: XML writers → ? OPlus frameworkloader → themeattrs → Settings
icon branch: icon-specific seed/MaterialStyle → a8.b scheme → icon XML/state
component-local branches: QS modes / Notification CONTENT / Media artwork / Volume capability
```

ownership规则：user change→native生成/刷新；module丢弃旧binding/generation并跟随，boot只观察。不能把用户手动变回TONAL_SPOT当异常自动修成EXPRESSIVE。

# 4. ColorOS 16 → ColorOS 17 delta

Old列为COE/旧实现假设；没有ColorOS16完整原始对照。

| Old assumption | ColorOS 17 reality | Evidence | Migration action |
|---|---|---|---|
| Overlay APK本身就是设计系统 | native组件/state/算法存在；旧资源存在不证明正确语义 | 02/01/03 +已完成分类只作上下文 | retire legacygeometry/surface payload |
| globalCardHook补齐native | native已有continuousgroups和smoothpath | 02 rawhelper/row | REPLACE component契约 |
| 全局删除divider更Expressive | divider有group/selected/fade/press含义 | 02 painter/caller | DELETE globalremoval |
| universalfieldremoval | S仍有mCardBackgroundColor | 02 definitions | 根因需actualfaulttrace，不猜field |
| 全系统只需style EXPRESSIVE | 多状态写端和不同consumer-local管线 | 01/03 | PARTIAL；尊重用户 |
| COE2025是必要算法升级 | native SPEC_2026 + CustomDynamicColors | 01/04 rawconstructor | DELETE engine replacement |
| media root/AOSPvolume/clock旧target足够 | media section细分、OPlusvolume、SimpleQsClock及独立clockpalette | 03/04 | REPLACE/RETARGET按契约 |
| 模块开机拥有theme | frozenservice在enable时每boot apply | 01 blocker / frozen source | 后续coding task改一次性用户请求 |

# 5. Implication for v0.2.0

## 5.1 Implementation blocker and prior hypotheses

**IMPLEMENTATION_BLOCKER — 用户style ownership，[OBSERVED]/HIGH**：冻结 `module/service.sh:192–195` 在native_expressive开启时每boot调用 `module/bin/coloros17-expressive-style.apply_style`；后者无用户后来修改的boot ownership guard。`restore_style`只比current==EXPRESSIVE不足以证明ownership，用户可主动重选同枚举。建议后续source变更：boot不写主题；明确用户操作才单次请求nativeapply；记录user/generation/expectedstate；用户change立即释放；无证明不restore。默认native_expressive=0不会触发，但不是启用后行为正确的证明。本分支不修代码。

[OBSERVED] `docs/P3_MD3E_SEMANTIC_ACCENT.md` 将67个资源归为high-confidence并映射system_primary；这是既有假设。当前结构分析没有证明14包全部consumer/alias/state，所以**不能把该数字当运行时验证结果**。`module/config/default.conf` 的md3e_semantic=1也不证明资源安全。Confidence: HIGH（文档/配置）；LOW（全量consumer）。建议下一实现任务对 `compat/coloros17/md3e_semantic_accent.tsv` 和 `tools/build_coloros17_semantic_accent.py` 的每条entry施加consumer/overlayability gate；本次不重复2938条资源分类。

## 5.2 Which RROs / which Hooks

| Category | Decision / verification gate | Confidence |
|---|---|---|
| OEM feature/navigation RRO | KEEP NATIVE；已有窄scope结论仅沿用handoff，不重新分析，不混入card体系 | HIGH政策；OEM具体行为是priorinput |
| old32 visual overlay / SystemUI single-dual/blur-Monet switching | REMOVE OLD OVERRIDE；不作为新设计本体，不copyAPK/资源值 | HIGH政策 + staticowner evidence |
| native-foundation correction RRO | migration/debug候选；clean native恢复后不默认叠加 | HIGH政策；需要legacy残留trace |
| newsemantic RRO | 仅经role consumer→resourcealias→overlayability/idmap→light/night/user更新完整验证的entries | HIGH契约；当前可发布名单UNKNOWN |
| CardHook/ListHook | REPLACE为精确tuple feature；当前segmented名单空；nativepath/divider保持 | HIGH |
| MonetColorSpec2025Hook | DELETE 全局生成替代；boot强制style也删除/改用户一次操作 | HIGH |
| QsLottieHook | REPLACE抑制器，目标仍QSIconViewProxy；default不清nativeLottie | HIGH |
| AospMediaCardHook | REPLACE：P binder/单control，不只改ROOT_CLASS，删除globalView/ImageView拦截/自造palette | HIGH |
| Font/MediaSeekBar | RETARGET精确SimpleQsClock/新root binding范围，签名/继承/role/lifecycle仍必须验证 | HIGH静态 / runtime MEDIUM |
| Volume/Notification/QSvisual | 分component再建contract；不得整块替换panel/card/blur/motion | HIGH |
| uncertainLauncher/Keyguard/framework features | NEEDS_EVIDENCE且默认关闭；scope外不移植 | HIGH政策 |

## 5.3 What to preserve / safe augmentation

KEEP NATIVE：geometry、group边缘/inset、smoothpath、divider状态、blur/translucency、icon artwork、alpha、navigation、press/haptics、native motion、template/panel拓扑、user/profile palette。

MD3E AUGMENT：已确认semantic角色的局部foreground/tint/state层；复用native当前palette，或遵循组件已经确认的native色源，不生产第二套系统动态色。motion/ripple/shape若未证明与native state/采样不冲突则DO NOT HOOK；设计名“Expressive”不构成证据。

禁止：global coui_round_corner_*、globaldivider透明、把每行改FULL、package-wideCard/List、genericMaterialicon替换原始geometry、globalViewbackground、globalScrim替换每组件blur、Pixel替代式锁屏/volume/media。

## 5.4 Migration order / implementation plan

[INFERRED] 后续source-level正式实现顺序，逐feature通过后才扩大：Confidence: HIGH（政策）。

1. 停止style boot重写与parallelMonet；让native恢复完整ownership，保留只读诊断。
2. retire旧package/globalgeometry/divider/card/32-overlay载荷；检查同module-id迁移确实无旧enabledoverlay残留；不重跑已完成分类。
3. 补Settings XML和faultprovenance，验证真实双背景门控/rowbinding；segmented白名单维持空，先nativegroup回归。
4. native主题切换协议验证：seed/style/configuration/XML/FRRO/user/light/night；补ThemeStyle parser和COUI loader，完善A5边界。
5. 对semantic TSV逐entry consumer准入；单target RRO验证overlayability、priority/idmap、native色更新；未验证entry不发布。
6. scoped registry先单Settings tuple/单control，加入完整signature/loader/role/state/generation/recycle门控。不要return-void patch当正式migration。
7. QS→Notification→Media→Volume→Clock逐组件验证；保留原生asset/blur/motion，只增加已准入语义属性。
8. 版本/用户/主题变更回归通过后形成v0.2.0发布baseline；未知项无通用fallback，不批量开功能。

# 6. Patch contract

本分支patch contract为reports-only；下表为未来实现的候选边界，全部mutation受缺口准入约束。

| Target class / method or source | Guard | Scope | Fallback |
|---|---|---|---|
| COUIPreference.onBindViewHolder / COUIListPreference / COUISwitchPreference | exact Activity+Fragment+adapter+key+view+layout/nativecard support | 单tuple，不修改position/path/divider | native；whitelist=[] |
| COUICardListSelectedItemLayout.refreshCardBg(int) | 完整tuple+已证明色角色、actual版本/loader | 单组件basefill，保持statewrapper | nativebasecolor |
| ThemeOverlayController.createOverlays(int) | nativehash/user/generation | diagnostic-only，DO NOT HOOK算法/FRRO值 | nativepalette |
| QSIconViewProxy.setIcon(State,boolean) | tileSpec/panelmode/actualloader/nativeasset+trace | diagnostic或单consumerrole；不可改共享state | nativeasset/tint |
| P b1.onBindViewHolder / onViewRecycled | media_card_section+插件实际loader+controlrole | 单controlbinding，root/surface/artwork不重建 | nativeplugin |
| OplusVolumeDialogImpl.onThemeChanged / OplusVolumeSeekBar | actualDI/capability/rowidentity/stream/state | 先诊断，semanticsetter需完整role独立准入 | nativepanel/slider |
| NotificationBackgroundViewExtImp.setDrawableMaterialColor | entry/cardtype/noColorized/mode/capability | 诊断，不统一替换notificationbackground | native各模式 |
| module/service.sh / expressive helper | 后续实现显式用户动作、user/generationownership证明 | boot只观察，不重复apply/restore | 不写用户主题 |
| semanticRRO build entry | exacttarget+role+alias+overlayability+用户主题回归 | 只有批准resource；不以coui/primary名字通配 | 不生成/启用该entry |

短伪代码（派生规格，不是厂商源码）：

```text
contract = registry.lookup(exactComponentIdentity)
if !contract || !allSymbolsResolved || !roleAndLayoutVerified: return native
if userThemeChanged: discardModuleState; followNativeGeneration
if classLoaderOrBindingChanged: disableUntilRevalidated
applyOnlyOneApprovedProperty(currentNativeColor, thisBoundComponent)
```

# 7. Failure/fallback behavior

[INFERRED] 合同缺任一证据时fail closed，不猜类名/field/enum，不改一半margin/path后吞异常，不从Settings错误扩展package范围，不从blur失败推断需统一solidcolor。native用户选择、disabled/pressed/selected/accessibility和systemfallback均保留。Confidence: HIGH。

未证overlayability则不安装RRO；nativegeneration/loader变更使旧hookstate失效；runtime诊断不记录用户内容。没有设备证据时本报告不会给“18项全部运行验收通过”的结论。

# 8. Unknowns

## 8.1 Acceptance answers — 18 questions

| # | 当前答案与证据类型 / confidence | 未闭合证据 |
|---|---|---|
| 1 Monet谁生成 | UXDesign候选/UI/XML；SystemUI ColorScheme生成公共palette/FRRO，Applier激活。[OBSERVED]/HIGH | COUI loader + commit成功trace |
| 2 EXPRESSIVE在哪里进算法 | U Style→v6.b→Google Variant；mono MaterialStyle→a8.b→r0→OPlusVariant；M2 ID3→SchemeExpressive/SPEC_2026。[OBSERVED]/HIGH | Androidstringparser原始定义 |
| 3 用户换主题谁重生成 | nativeUXDesignapply+SystemUI secure/wallpaper/contrast/usercallback；Ex可回调provider写wallpaperXML。[OBSERVED]/HIGH | 各设备gates/update顺序trace |
| 4 Settings整张group如何组成 | RecyclerView每行背景，nativeposition只圆组边缘；不证明外包统一container。[OBSERVED]/HIGH | layoutXML |
| 5 位置谁定 | COUICardListHelper parent/visible-neighbor/card-support；SettingsLib adapter另一门控。[OBSERVED]/HIGH | 实际gate值trace |
| 6 divider谁画 | Decoration准入→COUIRecyclerView.ItemDecoration painter；manager管pressalpha。[OBSERVED]/HIGH | 各screen安装/状态trace |
| 7 mCardBackgroundColor为何失效 | S仍存在；具体NoSuchFieldError加载来源未知。[OBSERVED]反证/HIGH；根因[UNKNOWN]/LOW | exactfaultstack/hash/loader/declaringclass |
| 8 Card/List该Hook哪些页面 | 当前无可启用segmentedtuple；保留native，未来完整tuple准入，禁止整包。[INFERRED]/HIGH政策 | screenkey/layout/bindingtrace |
| 9 QS色/shape/动画/Lottie | interactor/pool→drawable/outline/iconstate；QSIconViewProxy/QSLottieAnimationView；nativepresshelper。[OBSERVED]/HIGH | actualvariant/底部OpUtils/rippletrace |
| 10 Media属谁 | P拥有该template pager/section/artwork/background；host拥有数据/边界；不外推全ROMmedia。[OBSERVED]/HIGH | activeXMLroot/loadertrace |
| 11 Volume真实结构 | OPlus controller→View+Adapter→Row→SeekBar+materialhost+blur/anim层。[OBSERVED]/HIGH | DI/newhelperdefinitions/trace |
| 12 每组件动态色 | 五组件sources独立表见03§2.7。[OBSERVED]/HIGH（已追段） | QS/Media/Volume全部alias/upstream未完成 |
| 13 Monet2025 Hook还应存在 | DELETE全局替代，nativeSPEC_2026已实证。[INFERRED]/HIGH决定 | 原机覆盖日志仅验证规模，不改变架构决定 |
| 14 QsLottie retarget何处 | 当前目标仍QSIconViewProxy；无retarget证据，REPLACE抑制行为。[OBSERVED]/HIGH | nativeasset/varianttrace |
| 15 native保留哪些 | geometry/group/blur/translucency/artwork/alpha/nav/motion/state/component结构。[INFERRED]/HIGH | 各feature回归 |
| 16 MD3E能安全加哪些 | 只有已验证componentrole的局部semantic增强；没有全局shape/ripple/motion准入。[INFERRED]/HIGH契约 | 具体semanticentry runtime准入 |
| 17 用哪些RRO/Hook | OEM保持；legacyglobal删除；semanticentries逐项gate；scoped契约见§5/6。[INFERRED]/HIGH | 可发布entry名单需XML/idmap/trace |
| 18 旧逻辑删哪些 | globalcorner/divider/card/packageCard/List、parallelMonet、bootstyleforce、旧globalicon/surface/blur/单双色overlay切换。[INFERRED]/HIGH | 迁移残留/安装回归 |

## 8.2 Minimal evidence requests and release gates

仅以下三种缺口标签；不是请求公开上传vendor材料：

| Required evidence | Missing / why | How to close / gated feature |
|---|---|---|
| NEEDS_RUNTIME_TRACE | NoSuchFieldError与S字节码矛盾；缺actual目标来源 | 完整stack+process+actualclass/superfields/loader/APKhash；锁定故障包。Gate：Card/List字段兼容 |
| NEEDS_RESOURCE_XML | Settings/Media/QS layout/styles与resourcealias未在filteredtext | 精确相关XML/resolvedattrs，绑定screenkey/root/role。Gate：segmented/semanticRRO/ripple |
| NEEDS_RAW_BYTECODE | android.content.theming.ThemeStyle、OPlus资源loader、OpUtils、新volumeDI/helper、Mediaupstream部分跨界 | 按报告symbol补小范围类definition，重验caller与parser/aliases。Gate：完整theme/migration契约 |
| NEEDS_RUNTIME_TRACE | 当前用户主题切换、commit、COUIresource更新与五组件state/loader未采集 | native对照下读取secure/configuration/XML摘要/overlay/resolvedcolor；用户change→reboot不重写。Gate：A5提升为SAFE/ownership回归 |
| NEEDS_RUNTIME_TRACE | overlayability实际idmap/priority/残留oldmodule、component绑定/回收/accessibility | 单feature安装/回退只在未来实现阶段；先原生trace。Gate：v0.2.0发布 |

这些材料缺失使运行验收尚未完成；四份报告已提供可复现静态证据与明确实施边界。后续先补证、再实现最小feature，不以大规模UI重写验证猜测。
