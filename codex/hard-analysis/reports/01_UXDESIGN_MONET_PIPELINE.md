# 1. Executive conclusion

[OBSERVED] UXDesign 自身确实生成 native Monet **候选调色与预览数据**：`UxColorManager.initColorScheme`→`ra.m`→`v6.*`→Google libmonet Variant/tonal palettes；EXPRESSIVE 进入算法的位置可追到 `v6.b.<init>`。但 **Settings/SystemUI 最终 framework 动态资源的生成、FRRO 注册/激活完整链不在 UXDesign APK 内得到证明**。不能把预览算法存在当作 UXDesign 自己负责所有 FRRO。Confidence: HIGH（本地算法）；LOW（下游完整激活 owner）。

[OBSERVED] `a8/b` 的 MaterialStyle→OPlus utilities Variant 分派得到精确恢复；其可见 caller 属于单色图标链 `db.h`→`z7.b`，不是已证明的全系统 theme-style converter。系统主题 UI 的 Google style 选择与 MaterialStyle 图标选择分属不同状态。**未证明 Android theme-style string、MaterialStyle、libmonet Variant 是一个三列一一对应表。** Confidence: HIGH。

[OBSERVED] UXDesign 会写 Settings.Secure JSON、OPlus configuration/material_color_value、多类 XML、版本和 follow-wallpaper 状态。online XML 是下载/迁移分支，不能误报为每次 EXPRESSIVE 都生成 online XML。Confidence: HIGH。

[INFERRED] A5 结论为 **PARTIAL**：只改 `theme_customization_overlay_packages` 的 style，触及了 native apply 的一个输入，却不等同于完整 ColorOS apply；当前包不能证明它会同步所有 COUI/XML/consumer。对用户 ownership 而言，每次开机重写是明确不合格的方案。Confidence: HIGH（不同于 native 完整操作）；MEDIUM（单字段实际有效范围）。

# 2. Observed facts

## 2.1 Evidence provenance

U：`uxdesign/UXDesign.apk` SHA-256 `324080bc89384e12bff294ccbbffad19249cd2cfd6e8b70b7eea61e1c726d137`，与用户指定值及包内 manifest 相符。分析两个 DEX；jadx 1.5.3 辅助，Androguard 4.1.3 核对原始 definitions、invoke、field 和 switch。严重 jadx 恢复失败的方法（`SystemColorApplyUtil.e`、provider.call）不能按占位代码解释。PC 为方法内字节偏移。私有中间文件仅位于 `/tmp/coloros17-hard-analysis/`。

S/SR：Settings DEX/资源表哈希和基线见 [Settings 报告](02_SETTINGS_GROUPED_CARD_MODEL.md)。SystemUI consumer 的逐组件证据在 [SystemUI 报告](03_SYSTEMUI_COMPONENT_MAP.md)；本报告不提前把它们认定同源。

## 2.2 系统主题与 wallpaper 候选算法

| [OBSERVED] Symbol | 实际职责与证据 | Confidence |
|---|---|---|
| `UxColorThemeController.k():Intent` | 返回 `com.oplus.uxdesign.color.ACTION_COLOR_SETTINGS`，package com.oplus.uxdesign；它是设置入口，不是 palette engine | HIGH |
| `UxColorViewModel.p(Context):WallpaperColors` | 有 WallpaperManager.getWallpaperColors(1) 与 bitmap→WallpaperColors 分支 | HIGH |
| `UxColorManager.initColorScheme(WallpaperColors,Context,boolean)` | 拷贝 primary/secondary/tertiary/hints；生成 TONAL_SPOT、SPRITZ、VIBRANT、EXPRESSIVE、MONOCHROMATIC 的五组候选；可写 prefs 缓存；null wallpaper 可读缓存 | HIGH |
| `initExpressiveStyleColor(WallpaperColors)` | `new ra.m(wallpaperColors,mIsDarkMode,uxcolor.monet.Style.EXPRESSIVE)`→calculateStyledColor | HIGH |
| `ra.m.<init>(WallpaperColors,boolean,Style)` | 调 `p(WallpaperColors,boolean)` 选 seed→整数 seed constructor；种子规则有色彩评分、fallback | HIGH |
| `ra.m.<init>(int,boolean,Style,double)` | style switch 选择 scheme；低 chroma/non-CONTENT 与 zero-seed 有 fallback；保存五个 tonal palette wrapper | HIGH |
| `ra.m$a` + `v6.b.<init>(t6.b,boolean,double)` | EXPRESSIVE switch case 4→v6.b；constructor PC `0x0` 读 Google `Variant.EXPRESSIVE`，PC `0xa2` 调 `s6.a.<init>` | HIGH |
| `calculateStyledColor(ra.m)` | 从 n/j/k/i/o 五个 wrapper 的 e() 取候选颜色；不是完整 android resource table 写入 | HIGH |
| Activity coroutine/Wallpaper listener→initColorScheme | `UxColorSettingActivity$initWallpaperColorSeeds$1.invokeSuspend` PC `0x36`；`...registerObserver$colorChangeListener$1$1` 同 PC；`UxWallpaperColorSettingFragment.registerObserver$lambda$9` PC `0x1e` | HIGH |

[OBSERVED] 系统候选 scheme mapping 为：SPRITZ→`v6.e`→NEUTRAL；TONAL_SPOT→`v6.g`→TONAL_SPOT；VIBRANT→`v6.h`→VIBRANT；EXPRESSIVE→`v6.b`→EXPRESSIVE；MONOCHROMATIC→`v6.d`→MONOCHROME；CONTENT→`v6.a`→CONTENT；FRUIT_SALAD→`v6.c`→FRUIT_SALAD；RAINBOW→`v6.f`→RAINBOW。这里右列是 **Google** `com.google.ux.material.libmonet.dynamiccolor.Variant`。Confidence: HIGH（constructor enum reads 与 switch）。

## 2.3 Android theme-style JSON 的实际选择逻辑

[OBSERVED] `SystemColorApplyUtil.e(Context,UxColorViewModel)` 使用 live ColorConfig 和 tint color，读旧 secure JSON，再调用 `common.p1.a(String oldJson,String source,String style,int accent,int palette)`。PC `0x100..0x140` 读取 theme-index map；PC `0x1c8` 调 JSON builder；PC `0x1d8` 写 `Settings.Secure.putString`。Confidence: HIGH。

| ColorConfig 分支 | 实际 source/style 结果 | Confidence |
|---|---|---|
| Google color，themeIndex 22 | home_wallpaper / SPRITZ | HIGH |
| Google color，themeIndex 23 | home_wallpaper / VIBRANT | HIGH |
| Google color，themeIndex 24 | home_wallpaper / EXPRESSIVE | HIGH |
| Google color，themeIndex 25 | home_wallpaper / MONOCHROMATIC | HIGH |
| Google color，未映射 index | home_wallpaper / TONAL_SPOT fallback | HIGH |
| Color group 或 custom | source/style 的实际分支与普通 Google-style不同：group index 非0可选 VIBRANT；默认 TONAL_SPOT；此处不是 MaterialStyle.valueOf | HIGH |
| 非 group/custom/Google 的分支 | preset / TONAL_SPOT | HIGH |

`p1.a` 更新 `_applied_timestamp`、`material_you_overlay_enable=1`、`color_index=0`、`system_palette`、`accent_color`、`color_source`、`theme_style`，移除 color_both；保留可解析旧 JSON 的其他字段。`e` 另写 `oos_theme_customization_two_tone`。这里是 **UI 选项→Android style string**，不是已证明 **Android style string→MaterialStyle**。Confidence: HIGH。

## 2.4 MaterialStyle 精确分派：独立单色图标管线

[OBSERVED] `db.h.w(Context,MaterialStyle)` 分别调用 `z7.b.a(Context,int,Boolean,MaterialStyle)` 缓存 light/dark；后者 PC `0x12` 调 `a8.b.e(Context,int,boolean,MaterialStyle)`。`a8.b.e` 创建带 seed 的 DynamicColorsOptions，调用 b，再调用 a，返回 `b8.a` 图标色数据。`a8.b.c(Context)` 读 UiModeManager.getContrast()。Confidence: HIGH。

`a8.c.$EnumSwitchMapping$0` 和 `a8.b.b(MaterialStyle,boolean,Context,a8.a)` 的 switch，加上各 utilities constructor PC `0x0` 的 Variant enum read，证明如下映射。下面 Variant 是 **OPlus utilities** namespace，不是上述 Google Variant。

| MaterialStyle | switch case / scheme | `color.utilities.Variant` | Confidence |
|---|---|---|---|
| CONTENT | 1 / q0 | CONTENT | HIGH |
| EXPRESSIVE | 2 / r0 | EXPRESSIVE | HIGH |
| FIDELITY | 3 / s0 | FIDELITY | HIGH |
| FRUIT_SALAD | 4 / t0 | FRUIT_SALAD | HIGH |
| MONOCHROME | 5 / u0 | MONOCHROME | HIGH |
| NEUTRAL | 6 / v0 | NEUTRAL | HIGH |
| RAINBOW | 7 / w0 | RAINBOW | HIGH |
| TONAL_SPOT | 8 / x0 | TONAL_SPOT | HIGH |
| VIBRANT | 9 / y0 | VIBRANT | HIGH |

[OBSERVED] `db.h` 的图标样式读写 `ICON_MATERIAL_AND_SEED_COLOR_KEY` 和 seed，`MaterialStyle.valueOf` 从 icon-specific 序列化字符串取 style。`y9.q.a(Context,DesktopIconStyle,db.h)` 同样从 `getMIconSingleColor()` 解析。随后 `common.u.i(int,int,int,int,int)` 写 mono XML，`db.h.z(Context)` 保存 icon 配置。**没有证明更改 secure theme-style 就自动更改这个 MaterialStyle。** Confidence: HIGH（独立状态/caller）；UNKNOWN/LOW（三者自动同步）。

## 2.5 谁生成、保存、激活、消费

| 状态/产物 | Producer / persistence / activation / consumer | Evidence & Confidence |
|---|---|---|
| Google candidate palette | UxColorManager→ra.m→Google scheme；prefs 缓存；UI/ViewModel读取 | U constructor/caller 链；OBSERVED/HIGH |
| secure theme JSON | SystemColorApplyUtil.e→p1.a→Settings.Secure | U PC `0x1d8`；OBSERVED/HIGH。下游 FRRO owner 未证明 |
| OPlus material configuration | SystemColorApplyUtil.a→common.h.a builder，按 type/index 组合 flags；`d9.a.b(Configuration)`→IActivityManager.updateConfiguration；特定分支写 Settings.System `material_color_value` | U 调用链；OBSERVED/HIGH。framework 内部 resource reload 未给 |
| wallpaper COUI XML | `ta.f.d(ArrayList,int)`→c(File,ArrayList,boolean)；`o.g()/h()` 返回 `coui_theme_color_wallpaper.xml` / `_night.xml`，非主用户子目录 | U writer/path；OBSERVED/HIGH |
| custom COUI XML | `ta.a.e(int light,int night)`→d(File,ArrayList)→`o.a()/d()` 的 `ux_custom_color.xml` / `_night.xml` | U writer；OBSERVED/HIGH |
| mono icon XML | `common.u.i`→e(File,List)；`ux_color_master.xml` / `_night.xml`，写 `couiIconColorMasterForeground/Background` | U writer 与 db.h/y9.q caller；OBSERVED/HIGH |
| online COUI XML | online download/temp 管线；`UxColorUpdateService$a.g(Context)` 将 temp→root、清 temp、更新 configuration 与 online-version/state | U service；OBSERVED/HIGH。不是本地 Monet scheme output |
| COUI颜色名 | ta.e/ta.f 写 `couiSingleFirst*`、`NXcolorSingleFirst*` 等 groups/state roles | U serializer；OBSERVED/HIGH；runtime framework映射需原始loader |
| Settings消费 | 已追到 COUIContextUtil/theme attr `couiColorCardBackground/couiColorDivider` 与 native state drawable | S；OBSERVED/HIGH。generated XML→attr映射未完成 |
| SystemUI消费 | 不同组件的资源/MaterialSDK/Monet 路径独立核对 | 见03；禁止从U外推统一owner |

[OBSERVED] `UxColorSettingProvider` manifest authority 为 `com.oplus.uxdesign.uxcolor.material_setting_provider`，exported=true，但要求 `com.oplus.permission.safe.SECURITY`。`call` 含 ColorManager.initColorScheme、custom XML writer 等入口；不能假定普通模块有合法 API 权限或猜 method-string。Confidence: HIGH。

[OBSERVED] 两个 U DEX 的 invoke/field 索引未找到 FabricatedOverlay 直接调用；出现的 OplusOverlayManager 调用属于 language/app-name 分支。**这只说明本输入未见直接色彩 FRRO 构建，不证明 ROM 没有 FRRO。** Reflection/JNI/framework 跨界仍未知。Confidence: HIGH（检索限定）；UNKNOWN/LOW（全系统 FRRO implementation）。

# 3. Runtime flow

以下实线是静态可达链；`?` 为缺少证据的连接：

```text
WallpaperManager(home) / Bitmap → WallpaperColors
  → UxColorViewModel.p / Activity wallpaper listener
  → UxColorManager.initColorScheme
  → ra.m(seed selection, Style)
  → v6.b [EXPRESSIVE] → Google Variant.EXPRESSIVE → five tonal palettes
  → candidate colors / UI prefs
  → ColorConfig(themeIndex 24)
  → SystemColorApplyUtil.e → p1.a → secure theme JSON
  → SystemColorApplyUtil.a → OPlus configuration / material_color_value
  → ? framework color loader / FRRO builder / activation
  → ? framework dynamic resource table
  → Settings theme attrs / separate SystemUI consumers

Wallpaper/custom colors → ta.f / ta.a → /data/oplus/uxres/uxcolor/*.xml
  → ? OPlus resource loader → COUI theme attrs → Settings consumers

Icon seed + MaterialStyle → db.h → z7.b → a8.b.e/b/a
  → OPlus utilities scheme/Variant + contrast + light/dark
  → b8.a → common.u → ux_color_master*.xml + icon-specific settings
  → ? icon resource loader
```

[OBSERVED] 用户在 UXDesign 改颜色通过 UxColorSettingActivity 的 D0/G0 与 ViewModel 调 native apply；wallpaper callbacks 重算候选；provider 是另一受权限保护入口。online resource scheduling 的 UxColorUpdateManager/AutoCheckManager 是下载更新调度，不能称为所有 wallpaper/Monet 的唯一生成 owner。Confidence: HIGH。

# 4. ColorOS 16 → ColorOS 17 delta

没有旧版 DEX；old 列为冻结实现/COE 假设。

| Old assumption | ColorOS 17 reality | Evidence | Migration action |
|---|---|---|---|
| a8/b 是全系统 palette 中心 | 其确定 caller 是 mono icon helper；系统候选另走 ra.m | U call index + constructors | 分开 pipeline，禁止误 hook |
| enum 同名就是映射 | 有两套 namespace；SPRITZ→NEUTRAL、MONOCHROMATIC→MONOCHROME 证明名字并不统一 | SystemColorApplyUtil map、ra.m、a8.c | 使用实际分派；跨domain未证不补表 |
| 只写 theme_style 即完整 apply | native 同步 seeds/source/timestamp/enable/configuration/two-tone/follow flag | SystemColorApplyUtil.e/a/d | PARTIAL；先验证完整native入口 |
| online XML 就是 EXPRESSIVE output | online更新任务复制下载文件；wallpaper/custom/mono分别写其他XML | U writers/services | 正确分离 artifact ownership |
| libmonet存在证明UXDesign自己激活FRRO | 本DEX未见颜色FRRO直接调用；跨framework尾链缺失 | invoke index | NEEDS_RAW_BYTECODE |
| uninstall时尊重用户就够 | service在enabled时每次boot执行apply，会覆盖后来的手动选择 | 冻结service/helper源码 | REMOVE OLD OVERRIDE，见blocker |

# 5. Implication for v0.2.0

KEEP NATIVE：wallpaper seed scoring、Style/Variant 算法、contrast、user/profile 资源路径、configuration 更新和 UI 选择。MD3E AUGMENT：最终 consumer 已确认后采用有限 semantic resource layer，跟随用户当前 native palette；不生成第二套 palette，不强制全局 EXPRESSIVE。

A5 **PARTIAL**：secure style 是真实输入，但不能替代 OPlus 完整状态流；当前证据没有证明单字段更改可同时更新 COUI XML 与所有 SystemUI consumer。没有运行时 trace 就不标 SAFE。

**IMPLEMENTATION_BLOCKER — ownership（OBSERVED/HIGH）**：冻结 `module/service.sh:192–195` 在 SDK=37、native_expressive=true 时每次开机运行 helper `apply`；`module/bin/coloros17-expressive-style.apply_style` 无“用户后来改变选择”的 boot guard，直接写 EXPRESSIVE。默认关闭限制了触发条件，但用户启用后仍违反 ownership 要求。建议后续 coding task 改为明确用户操作的一次性请求；启动仅观测。`restore_style` 的 current==EXPRESSIVE 判断也无法区分用户主动重选 EXPRESSIVE 与模块仍持有 ownership；不能把枚举相等当成完整所有权证明。

[INFERRED] 最佳集成边界是 **native完成颜色更新之后的已验证组件消费者**；默认不拥有全系统 style。确需用户请求 native variant 时，优先 UXDesign 原生 UI 完整 apply，未经权限和参数验证不绕 provider。Confidence: HIGH（边界政策）；LOW（尚待选定唯一可调用native服务方法）。

# 6. Patch contract

| Target class / method | Guard | Scope | Fallback |
|---|---|---|---|
| `SystemColorApplyUtil.a(Context,UxColorViewModel,boolean)` | 精确APK hash/signature；完整ColorConfig生命周期；明确用户操作 | 仅观测native apply结束，不改返回/强制style；不是可公开调用服务 | 缺签名则不安装 |
| `UxColorManager.initColorScheme(WallpaperColors,Context,boolean)` | 当前用于诊断；不承担module palette | 观测seed/style/cache；DO NOT HOOK为全局替代算法 | 保留native |
| `a8.b.b(MaterialStyle,boolean,Context,a8.a)` | 仅mono-icon已验证consumer | DO NOT HOOK系统theme_style；不得强制EXPRESSIVE | 保留native |
| `COUICardListSelectedItemLayout.refreshCardBg(int)` | 02报告tuple准入 + color-role consumer验证 | 未来单组件semantic色；不改style ownership | 未准入完全native |
| `UxColorSettingProvider.call(String,String,Bundle)` | permission、method-string、bundle schema和user profile全验证前禁止写入 | 当前只读静态证据；不猜command | 不调用 |

短伪代码：

```text
onBoot: observeNativePaletteOnly()
onExplicitUserVariantRequest:
    if !verifiedNativeApplyContract: openNativeColorSettingsOrDoNothing()
    else nativeApplyOnce(); recordExpectedStateAndUserScope()
onNativeUserChange: relinquishModuleStyleOwnership()
onUninstall: restoreOnlyIfExactOwnershipStillProven()
```

不能在boot看到非EXPRESSIVE就认为需“修复”；用户选择是正常状态。

# 7. Failure/fallback behavior

[INFERRED] native apply API、权限、user profile、seed、style、configuration 或 palette consumer 任一缺证据时 fail closed：保留当前用户主题，不修改 secure JSON、XML、overlay state。颜色资源缺失时保留native fallback，而不是硬写替代颜色。Confidence: HIGH（契约）。

不复制生成文件跨用户；不写 online temp 文件冒充系统palette；不因类名/Variant相同就启用算法hook。不在本分析分支修复 shipping helper。

# 8. Unknowns

| Required evidence | 具体缺口 | 补充方式 |
|---|---|---|
| NEEDS_RAW_BYTECODE | secure theme-style string 到最终 framework palette/FRRO 的 parser、builder、OverlayManager activation；当前U只证明写端和候选算法 | 提供实际 ThemeOverlayController 的完整DEX、相关oplus-framework/services资源loader；追observer→transaction→resource consumer |
| NEEDS_RAW_BYTECODE | Android string→MaterialStyle 是否存在自动同步；已见两条独立链，无三者统一转换的证据 | 追secure observer与icon setting writer的调用链；若在framework，补对应类 |
| NEEDS_RESOURCE_XML | generated COUI XML→framework attr/resource mapping、完整styles引用；仅资源筛选text不足 | 相关OPlus loader XML schema、样例生成XML与resolved theme attrs；无需整个ROM |
| NEEDS_RUNTIME_TRACE | 用户换wallpaper/Google style/custom/online色以后各资源最终生成、激活与consumer更新，单字段写入究竟覆盖多少 | 只读比较secure/configuration/XML摘要、overlay list/idmap与resolved资源；按user/profile、light/dark采样 |
| NEEDS_RUNTIME_TRACE | ownership race、相同enum重选、module一次请求后的native用户改选 | 在明确用户操作边界记录状态generation；验证reboot不会重施加 |

A1/A3/A4 的本地生产与保存段已实证，framework激活与全部消费段明确未完成；不声称已形成无缺口的全系统data flow。后续功能实现受这些缺口约束。
