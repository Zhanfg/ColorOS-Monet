# 1. Executive conclusion

[OBSERVED] 本输入中的 SystemUI 包含 Android native Monet 的实际生成链：ThemeOverlayController→ColorScheme（SPEC_2026）→DynamicColors/MaterialDynamicColors/CustomDynamicColors→三FRRO→ThemeOverlayApplier。**它生成公共资源，不意味着所有组件都从同一资源读颜色。** QS、Notification、Media、Volume、Clock 是五个独立契约。Confidence: HIGH（静态链）。

[OBSERVED] QS 的资源配置、颜色state、drawable/path、icon asset及press feedback分别有owner。低模糊等级通知色另走 OPlus Material3ColorManager，固定选择CONTENT。Media的插件 section/adapter/view/controller 管理artwork、surface和沉浸背景，root自身只处理lifecycle/measure。Volume的panel/row/slider/material/animation分层存在，不能以AOSP VolumeDialogImpl作为迁移主假设。Confidence: HIGH（定义/caller）；MEDIUM（没有设备active-instance trace）。

[OBSERVED] blur至少有motion/ViewRoot、platform/posteffect、plugin背景RenderEffect与内容RenderEffect四种路径。radius资源只是参数；native blur capability、capture、混色与fallback不能由一组RRO统管。Confidence: HIGH。

[UNKNOWN] 当前设备DI选择、每个屏幕的真实实例树、plugin media root XML引用、全部颜色alias尾链未提供；本报告不宣称所有存在类均运行在当前页面。对应缺口见§8，未通过的augmentation必须关闭。Confidence: LOW。

# 2. Observed facts

## 2.1 Sources / evidence boundary

在仓库外用jadx 1.5.3阅读，Androguard 4.1.3核对definitions/invokes/fields以及恢复失败method。PC为method内字节偏移，code_off为对应DEX code item。只提交派生描述，不提交厂商源码/路径数据。SystemUI反编译有19处失败、plugin14处；失败占位抛异常不作为实际runtime行为。

| Alias / input | SHA-256 |
|---|---|
| M2 `systemui/classes2-monet.dex` | `7058b91822a69e273754854d25a605a0edde6ad54cde67973703fa9d18d58a08` |
| M3 `systemui/classes3-materialsdk.dex` | `86c686d407b1b3fa32471e7add88e9303f473d8f9acb69972ce16f55a0c4cde6` |
| M4 `systemui/classes4-oplus-components.dex` | `d8e93e9bca61eebcc923434c7585612e0706418a71687c4c9aa5e91daae3c5e2` |
| MR `systemui/systemui_resources.filtered.txt` | `f982a4076c469ec949aef111bcfab1717d29dfeadce1a496d213e6b97852e923` |
| P `systemui-plugin/classes.dex` | `79b863681ab8d77d925ac5fa122fc294becd528ea15cd146b8a186a0822a2ece` |
| PR `systemui-plugin/systemui_plugin_resources.filtered.txt` | `8097cb81d8612e139c78fb6ed756afa5b53d2b481755a6b77a75ec8c72f56250` |

[OBSERVED] M4中定义**1,081个** `com.oplus.systemui.plugins.qs.*` 类；P中未定义该prefix。因此namespace不能证明独立plugin APK ownership。`OPlusPluginClassLoader.loadClass(String,boolean)`（M2）对mPackages prefix走mBase，其他先super再fallback mBase；同名class object的actualloader仍需trace。Confidence: HIGH。

## 2.2 Public native Monet producer（不是全部consumer）

[OBSERVED] `ThemeOverlayController.start/fetchThemeStyleFromSetting/reevaluateSystemTheme/createOverlays`、light/dark schemes、三FRRO的注册/激活静态链，详见01 §2.6。`ColorScheme(List,boolean,int,double)` code_off `0x1fa06c` PC `0x76` 选SPEC_2026；raw packed-switch ID3 target `0x862`，new SchemeExpressive `0x866`、Variant.EXPRESSIVE `0x880`。ID8/9分别包含SchemeClock/SchemeClockVibrant算法分支，不能把它们当Clock View。Confidence: HIGH。

[OBSERVED] `ThemeOverlayController$$ExternalSyntheticLambda3.accept` 写 `android:color/system_<role>_light/_dark`；DynamicColors把palette/semantic/fixed/custom roles映射为名字。`MaterialDynamicColors.colorSpec` 初始化为ColorSpec2026；controller还保留OPlus neutral2_900特例。Android theme string的parser是外部 `android.content.theming.ThemeStyle`；其完整实现不在本输入。Confidence: HIGH（生成）；LOW（字符串parser全表）。

## 2.3 C1 — QS / Control Center

| Property | [OBSERVED] Owner / method / field / caller / DEX | Confidence |
|---|---|---|
| state源 | Android `QSTile.State`；`OplusQSHighlightTileView.onStateChanged(State)`复制state→post StateChangeRunnable；host tile服务与视觉不同职责 | HIGH / M2+M4 |
| tile root | M4 `OplusQSHighlightTileView`；`OplusQSHighlightTileViewImpl`继承并实现尺寸/padding；resizeable one/two-stage variants在M4的plugins.qs namespace | HIGH；当前panel variant MEDIUM |
| shape | `QSPersonalityRepository` shape flows→Std/Sep资源interactor→ResPool outline/shape flows；resizeable OneXOne/TwoXOne/TwoXTwo消费者分别读tile/highlight outline→transitionDrawable.setPathProvider | HIGH / M4 |
| drawable | `QSDrawableConfig`类型builder→`QSDrawableBuilder.build(View,boolean,Integer)`；GradientTileDrawable与MixColorTileDrawable是不同surface；TileDrawableWrapper持有delegate/path/userAlpha | HIGH / M4 |
| active/inactive | Std/SepQSTileResInteractor组合globaltheme、night、lowGaussian、superPower、colorful、two-tone，生成state configs→Std/SepQSResPool.updateTileViewDrawable等；不是固定Material palette单源 | HIGH / M4 |
| icon tint | TileIconColorState(active/inactive/unavailable/supportMask)→ColorStateList；OplusQSIconViewImpl/resizeable icon→QSIconViewProxy.setTintList→updateIconTint，按host drawableState选择色 | HIGH / M4 |
| icon animation | QSIconViewProxy.updateIcon保留Animatable2 start/stop及callback；setIcon采用asset及native调度；不是通用Material icon替换 | HIGH / M4 |
| Lottie | QSIconViewProxy持有QSLottieAnimationView；Companion.getLottieAnimAsset(Context,State)/(Context,int,String,int)，检查lottieSupport active bit16/inactive bit1；format string resource消费 | HIGH / M4 |
| Lottie runtime gate | setIcon code_off `0x32ce0c` PC `0x30`取asset；检查same spec、animationEnabled、shown、drawable、dialog/detail/allowed flag；PC `0x172` setTintColorfulConfig，后续播放；native对disable/reverse/cancel独立处理 | HIGH / raw M4 |
| press | OplusQSHighlightTileView构造attach PressFeedbackHelper.QsTilePressFeedback；touch DOWN/UP/CANCEL→COUIPressFeedbackHelper.executeFeedbackAnimator。不能再叠一套全局scale动画 | HIGH / M4 |
| shape deformation | TileDrawableWrapper.setDeformFraction(Float)→TileDrawableDelegate→PathCornerDrawable；Gradient/MixColor各处理色/混色transition；有deformation API不证明某MD3E morph已启用 | HIGH / M4；具体trigger MEDIUM |
| ripple | 上述nativepress路径已证实；该root上最终是否另有ripple/state overlay需layout/runtime核对。不能因无单一RippleDrawable调用就删除原生反馈 | UNKNOWN / LOW |

[OBSERVED] QS颜色source至少分三层：`QSFragmentHelper.applyAccentColor(Context)`→外部 `OpUtils.getThemeAccentColor/getDarkThemeAccentColor`→BaseQSResPool；Sep interactor activeColorFlow在colorful/globaltheme/two-tone/default之间选择；具体Gradient/MixColor和TileIconColorState供最终view消费。OpUtils定义未在切片，**Android system_primary → 所有QS active色的等式未证明**。Confidence: HIGH（中间/consumer链）；LOW（底部资源alias）。

[OBSERVED] MixColorTileDrawable持有AutoBlurDrawable；`updatePlatformMixConfig`→ViewBlurProxy.BlurConfig→applyBlurConfig，颜色与真实blur参数在这里合成；GradientTileDrawable.onStateChange/updateStateList通过ArgbEvaluator变色。更改shape或mask色可能同时影响blur配置，不能把它们当普通纯色card。Confidence: HIGH。

## 2.4 C2 — Notification

| Property | [OBSERVED] Owner / method / field / DEX | Confidence |
|---|---|---|
| stack / group / row | M2 NotificationStackScrollLayout、NotificationChildrenContainer、ExpandableNotificationRow/NotificationContentView；M4 OPlus stack/children/customrow extensions分别介入；普通/自定义/group/AOD不同契约 | HIGH |
| roundness / clip | Roundable/ExpandableOutlineView→ActivatableNotificationView.applyRoundnessAndInvalidate→backgroundNormal.setRadius(top,bottom,smoothflag)；NotificationBackgroundView.mCornerRadii→GradientDrawable，Ext.updateRadius；OPlusActivatableNotificationViewExImpl同步clip | HIGH |
| background | NotificationBackgroundView.setCustomBackground维护drawable callback/tint/radii；onDraw委托mExt.draw；NotificationBackgroundViewExtImp绑定nativeview，持viewBlurManager/materialColorManager/entry/blurMode/clip信息 | HIGH |
| blur / translucency | ViewBlurManager.requireBlurProxyForView(CardType,...)、resolveBlurMode、decideBlurType→ViewBlurProxy；headsup/keyguard/shade/custom/menu等不同CardType与material mode；alpha/mix并非单一color | HIGH |
| dynamic fallback色 | MaterialColorManager.resolveUxSnColor（code_off `0x1f7838`）PC `0x22` MaterialStyle.CONTENT，`0x2a` Material3ColorManager.getUxSn；get primary wallpaper seed，传night与tone | HIGH / raw M4+M3 |
| actual color consumer | NotificationBackgroundViewExtImp.setDrawableMaterialColor：noColorized+模糊等级条件→currentMaterialColor→bgView.setTint；colorized可保持row currentBackgroundTint；headsup/zero fallback `notification_material_background_color_compass` | HIGH |
| icon | M2 NotificationHeaderViewWrapper保持CachingIconView及original color；M4 OplusNotificationHeaderViewWrapperExImp.resolveHeaderViewsPlus/updateIconColor检测grayscale、appIcon、vector、notification.isColorized，原始icon或local资源分支→SRC_ATOP | HIGH；所有自定义RemoteViews LOW |
| expanded | ExpandableNotificationRow/NotificationContentView与ChildrenContainer维护展开layout/state；background expand-size/alpha和outline同步；不能用一个corner Hook统管 | HIGH |
| pressed / click | NotificationBackgroundView drawableStateChanged/hotspot→stateful drawable；OPlus NotificationClickEffectControllerImpl.startClickAnimation(row,...)含TalkBack门控；background ext独立clickAlpha/clickEffectDrawable | HIGH |

[OBSERVED] MaterialColorManager从home/keyguard wallpaper bitmap生成WallpaperColors，低Gaussian等级才触发相关coroutine；night tone分别30/95，button40/70，capsule有独立值。setCurrentColorsByState按keyguard/B等级选择再通知callbacks；因此 **通知的CONTENT fallback pipeline不受全局EXPRESSIVE字段一对一控制**。M3 getUxSn实际消费UxMaterialDynamicColors的OriginalAlgorithm.DynamicColor，与M2 Google SPEC_2026是不同namespace/用途。Confidence: HIGH。

[UNKNOWN] app RemoteViews内文字/图标由framework/app producer等提供；不能把wrapper一个分支推广为所有通知icon均Monet。资源筛选表不能证明全部alias最终落在system_*。Confidence: LOW。

## 2.5 C3 — Media（SystemUI + 独立P插件）

[OBSERVED] P `shared.template.section.media.MediaPlayerCardPageRootView` extends FrameLayout，**零自有field**；methods只有constructor/onAttachedToWindow/onDetachedFromWindow/onMeasure（code_off `0x246514`）。它不是surface/artwork/blur/colors算法owner。root XML实际引用未提供，不能宣称这个root一定是当前QS媒体卡实例。Confidence: HIGH（类职责）；LOW（当前实例）。

| Media layer | [OBSERVED] Owner / chain in P | Confidence |
|---|---|---|
| pager/adapter | `section.media.e1`绑定ViewPager2/COUIPageIndicator；`b1.onCreateViewHolder` inflate ID `0x7f0c0034 layout/media_card_section`→`c1`；onBind创建/绑定s1，recycle调用s1.dispose | HIGH |
| standard section | `section.media.s1`持containerView、K0 viewmodel、MediaBackGroundView、RotatableImageView、DirectionAwareSeekBar、LiveAlertTextView、OplusLottieAnimationView；constructor findViewById，不在root重建内容 | HIGH |
| surface/light | `s1.<init>`配置MediaBackGroundView(CustomLottieView)的shape、stroke；enable分支设置 `component.light.f` MultiLightDrawable，callback/update基于VM state；不是简单Material卡片 | HIGH |
| artwork | s1更新model bitmap→RotatableImageView.setEffectBitmap/g与native动画；immersive `Y0`绑定两SmartShapeableImageView→`section.media.e`背景controller.e(Drawable,boolean)双buffer/pending swap | HIGH |
| fullscreen background | `section.media.e`（jadx显示C0352e，报告以raw e为准）→renderer `r8.H4.h(model,animate)`→`component.media.view.q.a(Bitmap,...)`更新content/top/bottom mirrors；mask取model.c | HIGH |
| blur | q.setMaskColor(int)→两个BackdropBlurView.b；BackdropBlurView.b code_off `0x240158` PC `0x30` OplusRenderEffect.createGradientBlurEffect→setBackgroundRenderEffect；H4.i(true)另给content setRenderEffect(createBlurEffect) | HIGH |
| corner | MediaBackGroundView/CustomLottieView自己的shape/stroke；SmartShapeableImageView smoothCorner/imageShape；q1.getOutline仅**top-right icon** `media_card_top_right_icon_corner_size`，不是card总corner | HIGH |
| motion | RotatableImageView、SmartShapeableImageView、immersive/page animators、X0 transition callback、背景controllerpending state与dispose分别负责 | HIGH；当前variant MEDIUM |
| ripple / controls | s1.s(View)按VM flag保留/取消 `drawable/button_ripple_bg`；按钮action另有OplusLottieAnimationView；DirectionAwareSeekBar消费VM color model | HIGH |

[OBSERVED] PR `color/media_style_item_stroke_color=0x7f0604ef`、`dimen/media_card_stroke_width=0x7f070280`被s1 constructor消费；top-right icon corner `0x7f07028e`被q1消费，明确不是media root radius。s1的progress颜色取K0中flow包裹的media model a.a，再用 `coui_seekbar_progress_selector`处理；没有证据可将所有control色归为SystemUI FRRO。Confidence: HIGH。

[OBSERVED] Media的静态owner结论：**P确实拥有该template媒体视觉实现和具体绑定consumer**；host仍保留MediaCarousel/MediaData/播放器状态与plugin boundary。不能从一个P root断言ROM所有media（输出对话框、锁屏、QS fallback等）均由P画。mask color upstream字段生产以及root XML归属仍须补证。Confidence: HIGH（template实现）；MEDIUM（当前使用范围）。

## 2.6 C4 — Volume

[OBSERVED] M4 `OplusVolumeDialogImpl` implements VolumeDialog/OplusVolumeDialogInterface等，持mRows、mController、mState、mActiveStream、mOplusVolumeDialogView、repositories/abilities。`addRow` new OplusVolumeRow；init→OplusVolumeDialogView.initDialog；showH→view.showSliderVolume等；onStateChangedH→refreshRows/updateVolumeRowSliderH，音量行为与视觉分层。code_off分别 `0x4e47e8`、`0x4e4c04`、`0x4e5740`、`0x4e4f28`。Confidence: HIGH。

| Volume property | [OBSERVED] Owner / method / state | Confidence |
|---|---|---|
| panel/window | OplusVolumeDialogView.CustomDialog / mWindow/mDialogView；initDialog、expandPanel、showSliderVolume、dismissH；portrait/side/list topology由此管理 | HIGH / M4 |
| row | OplusVolumeRow.initRow，stream/uid/playerId、tracking/requestedLevel/ss、view/icon/slider/nameText/sliderFrame；多个音频流不是一份通用Material row | HIGH |
| adapter | VolumeListAdapter(ListAdapter)、panelShowList/sideShowList/volumeRowList、rowdiff、reparent和bound color；native回收/动画不得全局替换 | HIGH |
| slider | OplusVolumeSeekBar extends COUIVerticalSeekBar；constructor创建OplusVolumeBarMaterialHost、spotLight helper；onDraw→mMaterialHost.syncBeforeDraw；progress/supervolume/disabled独立 | HIGH |
| shape | OplusVolumeBarMaterialHost.syncElevationAndOutline/syncBeforeDraw调用OplusVolumeShapeGeometry等；VolumeBlurManager引用VolumeCornerSpec/SurfaceFactory契约。被引用的新helper定义不全，不能恢复全部corner计算 | HIGH（调用）；LOW（完整实现） |
| blur/background | View持VolumePlatformBlurSession/VolumePlatformBlurHostHelper，show/expand/detach调用prepare/capture/release；VolumeBlurManager.getVolumePanelBackground选择solid/platform/motion，构建BlurConfig、AutoBlurDrawable/ViewBlurProxy | HIGH（可见代码）；session内部 LOW |
| animation | PanelTransitionSession、PanelExpandPreludeAnimator、OplusVolumeSideShowSession、OplusVolumePanelAccessoryAnimator、VolumeItemAnimator + native seekbar thick/trans/touch动画 | HIGH（定义/调用）；完整session轨迹 MEDIUM |
| color | OplusVolumeSeekBar读取oplus_super_volume_gradient/oplus_volume_bar_progress_background/oplus_volume_coui_background；VolumeListAdapter消费oplus_volume_plane_text_color；native capability分支分别solid/mixed/background | HIGH；资源alias到Monet LOW |

[OBSERVED] slider数值ID已映射MR：`0x7f060d8d oplus_super_volume_gradient`；`0x7f060d97 oplus_volume_bar_progress_background`；`0x7f060d98 oplus_volume_coui_background`；adapter `0x7f060da2 oplus_volume_plane_text_color`。这些是直接consumer，不能因为名字含color或资源表有system_primary就声称全部nativeMonet。Confidence: HIGH。

[OBSERVED] `VolumeBlurManager.getVolumePanelBackground` code_off `0x4fea8c`：VolumeMaterialCapability.resolve决定solid/platform/motion；solid读native drawable；另建混色BlurConfig、VolumeCornerSpec，ViewBlurProxy和AutoBlurDrawable。`getVolumeBarBackground`（`0x4fea3c`）交VolumeSurfaceFactory。capability/factory/session/shape几类在此切片只有references，无完整definition。**AOSP主owner假设应弃用；OPlus实现链已证实，但OplusVolumeModule DI/当前active实例仍未知。** Confidence: HIGH（实现）；MEDIUM（当前runtime owner）。

## 2.7 C5 — 五组件真实色源分开记录

| Component / state | [OBSERVED] 已追到consumer的source | 仍未证明的尾段 | Confidence |
|---|---|---|---|
| QS | OpUtils accent→Base pool；colorful/global-theme local资源/two-tone→activeflow；Std/Sep pool→Gradient/MixColor/TileIconColorState→view/icon | OpUtils实现/全部resource aliases；当前panel gates | HIGH / tail LOW |
| Notification | lowGaussian wallpaper→Material3ColorManager.CONTENT→currentMaterialColor→Ext.setTint；colorized保留row tint；headsup/local fallback；icon原始/灰度本地色 | framework/app RemoteViews以及完整fallback alias | HIGH / tail LOW |
| Media template | P viewmodel/model palette field→progress；artwork→fullscreen背景，model maskColor；本地stroke/ripple resources | model color producer及active root XML；未证实使用M2全局scheme | HIGH / upstream LOW |
| Volume | nativeVolume resources/capability/material host→slider/row/panel；blurmix独立 | 新helper内部+resource aliases+active DI | HIGH / tail LOW |
| QS/statusbar Clock | SimpleQsClock→OplusQSClock→AOSP Clock；Clock.onDarkChanged→DarkIconDispatcher.getTint→mNonAdaptedColor→setTextColor；OPlus red-one可截取 | QS header另一层色设置/当前实例；无证据称SimpleQsClock直接读SchemeClock | HIGH / tail LOW |
| Clock palette algorithm | M2 ColorScheme ID8/9含SchemeClock/Vibrant branches，与view不是同一owner | native fetchThemeStyle允许列表不含8/9；锁屏具体consumer/variant路径需补 | HIGH / consumer LOW |

## 2.8 C6 — 真正 blur API 与资源参数

[OBSERVED] M4 shared `ViewBlurProxy` 按BlurType选择motion、platform-static、blend-wallpaper；setBlurAmount/applyBlurConfig与enable/lifecycle独立。

| Layer | [OBSERVED] Runtime API / caller | 资源角色 / limitation | Confidence |
|---|---|---|---|
| motion | `blurability.motion.MotionBlurHelper.ensureBlurDrawable`→ViewRootManager.getBackgroundBlurDrawable；setBlurParams/setBlurRadius/setCornerRadius；BlurUtils.applyBlur调用SurfaceControl.Transaction.setBackgroundBlurRadius或OplusBlurManager同API | radius是输入，window supportsBlurs/lifecycle/gates另决定是否渲染 | HIGH |
| platform | `blurability.platformblur.PlatformBlurDrawable.applyBlurConfig`→com.oplus.posteffect.BlurDrawable.setBlurParamsSync；BlendParam/materialParams、foreground/mask/stroke/smooth path分层 | BlurConfig与platform manager/capture参与；dimen不能替代engine | HIGH |
| QS/notification | MixColorTileDrawable/ViewBlurManager→ViewBlurProxy→上述共享能力；不同CardType/gates | fallback color不等于实时blur | HIGH |
| Volume | VolumeBlurManager + bar material host→AutoBlurDrawable/ViewBlurProxy；platform session管理capture的调用可见 | session/helper定义缺失，不能声称已证实capture内部算法 | HIGH调用 / LOW内部 |
| plugin background | BackdropBlurView→OplusRenderEffect.createGradientBlurEffect→OplusViewBackgroundRenderEffect.setBackgroundRenderEffect | 真背景effect，不是blur_radius字符串推断 | HIGH |
| plugin content | H4.i与animation helper→View.setRenderEffect(RenderEffect.createBlurEffect) | content blur与backdrop blur不同采样对象 | HIGH |

# 3. Runtime flow

实线表示静态可达，`?`表示缺证；不冒充现场trace：

```text
native palette: UXDesign secure JSON / wallpaper / contrast
  → ThemeOverlayController → ColorScheme SPEC_2026
  → DynamicColors + fixed/custom → android FabricatedOverlay → commit

QS: theme/config/personality/panel-mode repositories
  → Std/Sep interactors → resource pools (drawable / outline / icon color)
  → host & resizeable tile → QSDrawableBuilder / TileDrawableWrapper
      ├ state/geometry/deformation/press native owner
      └ icon → QSIconViewProxy → drawable or QSLottieAnimationView

Notification: wallpaper/home/keyguard + level/mode
  → MaterialColorManager → M3 CONTENT getUxSn → currentMaterialColor
  → NotificationBackgroundViewExtImp.setDrawableMaterialColor → setTint
  → ViewBlurManager → ViewBlurProxy → motion/platform render APIs
  + row/group/roundness/expand/notification icon paths remain separate

Media: host data/plugin boundary → ? active XML root
  → P e1 pager → b1 layout/media_card_section → c1 → s1 + K0
      ├ MediaBackGroundView / MultiLightDrawable / local stroke
      ├ RotatableImageView artwork + DirectionAwareSeekBar + native buttons
      └ immersive Y0 → e controller → H4 → q bitmap/mask
          → BackdropBlurView → OPlus background RenderEffect

Volume: ? current DI selection → OplusVolumeDialogImpl
  → rows/state → OplusVolumeDialogView + VolumeListAdapter
  → OplusVolumeRow → OplusVolumeSeekBar → bar material host
  → capability/background factory/session references + native blur APIs
  → native panel/side/row transition sessions

Clock View: DarkIconDispatcher → Clock.onDarkChanged
  → textColor / OPlus clock styling
Clock scheme: ColorScheme ID8/9 → palette (distinct from View chain)
```

# 4. ColorOS 16 → ColorOS 17 delta

Old列是COE/项目假设，没有ColorOS16完整DEX做二进制比较。

| Old assumption | ColorOS 17 reality | Evidence | Migration action |
|---|---|---|---|
| SystemUI全组件共享一种Monet色/shape | 五组件有独立state/consumer/source | 上述M2/M3/M4/P调用链 | 拆分contract |
| SimpleQSClock | SimpleQsClock extends OplusQSClock→Clock | M4 definitions | RETARGET精确大小写；不改全部TextView |
| old media root是surface owner | P新root只lifecycle，pager/section/artwork/background不同类 | P defs/callers + PR layout | REPLACE旧重建hook |
| plugins.qs包名证明P加载 | M4定义1,081个该prefix类；实际loader仍须trace | DEXdefinition + OPlusPluginClassLoader | 使用actualclassloader |
| AOSP VolumeDialogImpl主owner | OPlus controller→view→row→slider/material契约已存在 | M4调用；DI缺口明确 | 删除AOSP替换假设 |
| blur_radius就能改blur体系 | ViewRoot/posteffect/RenderEffect三类真实API与capability/采样不同 | M4/P API invokes | KEEP NATIVE |
| 需COE补2025全局色算法 | native SPEC_2026，另有custom/fixed/OPlus特例 | M2 raw ctor/controller | DELETE Monet replacement |

# 5. Implication for v0.2.0

[INFERRED] C7候选增强边界如下；**当前不授权变更未通过trace的consumer**。Confidence: HIGH（政策），MEDIUM（候选插入位置）。

| Component | KEEP NATIVE / DO NOT HOOK | MD3E AUGMENT / HOOK HERE candidate |
|---|---|---|
| QS | tile geometry/path、active-state语义、Lottie/icon artwork、nativepress与deformation、blurcapture | verified单tile foreground/状态色consumer；native state更新之后观测；不叠globalripple/morph |
| Notification | group/roundness/RemoteViews/colorized/heads-up/expand/blur/click/TalkBack | 确认非colorized、非custom、非AOD的具体action semantic-role；不能覆盖background mode |
| Media | artwork-drivensurface、localshader、rootsection拓扑、immersive动画、nativebuttons/lyrics/seek | verified单control语义色/state-layer；沿binder与recycle管理，不在root换card |
| Volume | controller音量语义、side/panel/row拓扑、shape/capture/haptics/expand/seekbar motion | 对已确认单control前景读取当前native色；不换slider/materialsurface |
| Clock | red-one、字体比例/导航触摸、DarkIconDispatcher对比度；SchemeClock不是目标View | 唯一实例且颜色门控验证后允许语义foreground；无globalfont/clockreplacement |

RRO仅用于被consumer证明且独立可overlay的有限semantic resources；不能全局替换oplus/coui corner/divider、shader/artwork、motion/alpha/blur颜色。当前没有完整XML/overlayability/idmap，不列“已可发布”的新RRO。

# 6. Patch contract

这些契约区分诊断与未来augmentation，未批准条目不安装mutation。

| Exact target class / method | Guard | Scope | Fallback |
|---|---|---|---|
| ThemeOverlayController.createOverlays(int) | native hash/signature/user/palette generation | 诊断，DO NOT HOOK返回/FRRO values | native |
| QSIconViewProxy.setIcon(QSTile.State,boolean) | actualloader+tileSpec+panel mode；诊断或完整单tile role准入 | 仅观测调度；禁止清lottiePrefix/support | 原始state与asset |
| TileIconColorState.getColorStateList(Integer) | 该model已确定唯一tile绑定；复用flow/model不允许全局修改 | future单consumerforeground，native base states完整 | nativeColorStateList |
| NotificationBackgroundViewExtImp.setDrawableMaterialColor() | entry、rowmode、noColorized/heads-up/capability匹配；仅diagnostic | 追色源，不统一改bg tint | native模式 |
| OplusNotificationHeaderViewWrapperExImp.updateIconColor() | grayscale/appicon/vector/colorized全部核对 | DO NOT HOOK原始icon geometry；目前仅诊断 | nativeicon |
| P b1.onBindViewHolder(RecyclerView.ViewHolder,int) / onViewRecycled | exactpluginloader/root layout/schema；s1control身份/role完整 | future单controlsemantic绑定；当前诊断 | nativebinder/recycle |
| P BackdropBlurView.b() | effect能力与采样路径，native fallback | DO NOT HOOK全局radius/effect；仅诊断 | nativegradient background |
| OplusVolumeDialogImpl.onThemeChanged()/onStateChangedH(State) | actualDI/viewinstance/user/stream；不影响音量数据 | 诊断更新generation；component role另准入 | nativepanel |
| OplusVolumeSeekBar.onDraw(Canvas) / material host syncBeforeDraw | 不变形/shape/capture；仅诊断，不能每frame改全局色 | futureconsumer色需单独可调用setter且完整state验证 | nativepaint |
| Clock.onDarkChanged(ArrayList,float,int) | 唯一SimpleQsClock实例与red-one/contrast验证 | 诊断；futureforeground不越过DarkIconDispatcher | nativecontrast |

[INFERRED] motion/ripple/shape/state-layer插入必须在native state owner的同一绑定生命周期，验证不会重复press或替换原生描边/blurmask；若无法满足，则只保留native功能。Confidence: HIGH（契约）。

# 7. Failure/fallback behavior

[INFERRED] 缺class/method/field/resource/loader/mode任一则该feature fail closed；不猜AOSP替代、旧media namespace或“相似”blur API。plugin reload解绑、native theme update清旧generation、recycle不保留view state。未知coloralias时使用nativefallback，禁止写死模块palette。Confidence: HIGH。

观察到blur helper异常并不授权把整个card变solid；能力等级/省电/全局主题/可访问性fallback由native owner保持。未完成di/capture/overlayability验证不能标feature SAFE。

# 8. Unknowns

| Required evidence | 具体缺口 / 原因 | 最小补充 |
|---|---|---|
| NEEDS_RAW_BYTECODE | 外部OpUtils主题accent方法、android.content.theming.ThemeStyle parser、OPlus XML resource loader | 提供相应framework/common类，追resourcealias，勿上传完整ROM |
| NEEDS_RAW_BYTECODE | OplusVolumeModule DI、VolumePlatformBlurSession/HostHelper、VolumeSurfaceFactory/CornerSpec/Capability/ShapeGeometry部分仅references | 补这些类definition，确认constructor与capability/render lifecycle |
| NEEDS_RESOURCE_XML | media_card_section实际root类/完整styles，QS ripple布局、通知RemoteViews/framework模板与alias | 有限XML+resolvedattr，resource筛选text无XML内容 |
| NEEDS_RUNTIME_TRACE | Std/Sep/resizeable tile实际选型、press/ripple/deformation、actualclassloader，不能仅用plugins包名 | 原生实例树+绑定state/loader/主题mode；按tile状态采样 |
| NEEDS_RUNTIME_TRACE | Notification各CardType/lowGaussian/headsup/group/colorized的真正activeconsumer与icon分支 | 记录entry→row→background→proxy→mode/source；不采集用户通知正文 |
| NEEDS_RAW_BYTECODE | Media VM model mask/control color字段的完整producer/host-service跨界，未证实FRRO映射 | 按K0/model caller追流；raw恢复失败构造，必要时补host service类 |
| NEEDS_RUNTIME_TRACE | P template是否当前media主surface、rootxml实际实例、pluginreload和artwork/immersive切换 | host+plugin loader日志/adapter绑定及原生截图，无vendor drawable dump |
| NEEDS_RESOURCE_XML | Volume本地颜色在当前theme/light/night的完整alias/overlayability；Clock header的完整色链 | 有限color/style XML与resolvedresource，之后确定RRO是否可用 |
| NEEDS_RUNTIME_TRACE | Volume当前DI/side/panel/capture/haptic/seekbar状态、Clock实例与nativecontrast | 原生过程只读trace；不先改UI来验证假设 |

结构图回答静态ownership；未知项阻止相应Hook/RRO上线，不用猜测替代验收证据。
