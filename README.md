# ColorOS Monet

ColorOS Monet 是一个面向 ColorOS、OxygenOS 及常用 Android 应用的动态配色组件系统。

当前版本不再把莫奈适配打包成一组静态 Overlay APK，也不再依赖把第三方模块文件直接挂载进系统。核心改为：

- **Rust 运行时 `monetctl`**：负责组件校验、安装、启停、应用和壁纸色变化监听。
- **`.cmonet` 组件包**：带固定文件头、清单摘要和载荷摘要，可供后续 WebUI 直接识别。
- **Fabricated Runtime Resource Overlay（FRRO）**：优先通过 Android OverlayManager 动态注册资源，不向模块中塞 APK。
- **`SKIPMOUNT=true` 模块基座**：Magisk、KernelSU、APatch 只负责生命周期启动，不挂载系统目录。

## 设计灵感

界面的视觉层级、深色表面、圆角卡片和动态强调色处理，灵感来自项目所有者提供的 **COE 2.5、COUI Expressive 与 Material 3 Expressive 社区界面参考**。COE 2.5 只用于能力和交互分类研究，详见 [`docs/COE_2_5_REFERENCE.md`](docs/COE_2_5_REFERENCE.md)。

这里只标注灵感来源：**没有复制参考界面的图片、图标、代码、布局文件或专有资源。**

## 已重新实现的组件

### ColorOS / OPlus / OnePlus

共 31 个 ColorOS/OPlus/OnePlus 目标组件，包括：

- 设置、SystemUI 四种样式、无线设置、桌面、电话、联系人、时钟；
- 相机、电池、权限、安全中心、手机管家、通知管理；
- Breeno、儿童空间、护眼、Car Connect、OShare；
- 辅助球、实时字幕、跨屏、Linker、并行空间等。

`coloros-settings-full` 包含此前单独修正的卫星网络入口资源，图形为项目独立重画，配色接入系统动态色。

### Scene 与微信

- `scene-monet`
- `wechat-monet`
- `wechat-bubble-pro`
- `wechat-classic-bubble`
- `wechat-multiscene-corners`
- `wechat-solid-tab`

### 常用应用

- `x-monet`
- `tim-monet`
- `coolapk-monet`

总计 **40 个 `.cmonet` 组件**。

## 清洁重构边界

仓库不包含：

- X、TIM、酷安、微信、Scene 或 ColorOS 原始 APK；
- 从其他模块复制的 Overlay APK；
- 第三方矢量路径、位图、字体或签名文件；
- 密钥、Token、Cookie、证书私钥。

旧模块只作为行为和兼容目标对照。37 个历史二进制目标已被重新表达为独立组件源文件；项目自绘图标采用小型几何图形词汇，复杂容器按语义重建。无法安全等价迁移的空字符串、`id` 定义以及单个复杂 `array/style` 会记录在各组件的 `unsupported.tsv`，而不是伪造“完整兼容”。

## 组件格式

每个组件以 `CMONET01` 开头：

```text
0x00  8 bytes   magic: CMONET01
0x08  2 bytes   format version
0x0A  2 bytes   header size: 128
0x0C  4 bytes   flags
0x10  8 bytes   manifest length
0x18  8 bytes   payload length
0x20 32 bytes   SHA-256(manifest)
0x40 32 bytes   SHA-256(payload)
0x60 32 bytes   reserved, must be zero
```

详细定义见 [`docs/COMPONENT_FORMAT.md`](docs/COMPONENT_FORMAT.md)。

## 构建

```bash
python tools/build_component_sources.py
python tools/compile_component_assets.py \
  --sources build/component-src \
  --output build/component-compiled \
  --aapt2 "$ANDROID_SDK_ROOT/build-tools/35.0.0/aapt2" \
  --android-jar "$ANDROID_SDK_ROOT/platforms/android-35/android.jar"

cargo build --manifest-path runtime/Cargo.toml --release
python tools/build_components.py \
  --monetctl runtime/target/release/monetctl \
  --sources build/component-compiled
```

正式模块由 CI 交叉编译 ARM64 Android Rust 运行时后打包。临时 APK 只在构建阶段用于把独立 XML 编译为 Android Binary XML，**不会进入模块或 `.cmonet` 产物**。

## 设备端管理

```sh
# 查看组件
/data/adb/modules/coloros_monet/bin/monetctl list

# 启用或停用单个组件
/data/adb/modules/coloros_monet/bin/monetctl enable tim-monet
/data/adb/modules/coloros_monet/bin/monetctl disable tim-monet

# 重新应用全部已启用组件
/data/adb/modules/coloros_monet/bin/monetctl apply-all
```

模块 Action 会在“全部停用”和“恢复默认组件”之间切换。状态位于：

```text
/data/adb/coloros-monet/
```

## 兼容性说明

FRRO 仍受目标应用的 `overlayable`、签名、actor 和分区策略约束。ColorOS 固件或第三方应用可能拒绝某个目标，不能因为组件成功打包就宣称设备端必然生效。

设备验证应检查：

```sh
cmd overlay list --user 0
cmd overlay dump com.android.shell:<overlay_name>
cat /data/adb/coloros-monet/service.log
cat /data/adb/coloros-monet/watcher.log
```

对被策略拒绝或必须修改运行时行为的目标，项目预留单一的 `zygisk-resource` 行为桥接层；它不会为每个目标分发 APK。该桥接层尚未完成，因此当前公开版本不会把资源覆盖描述为完整的 COE 类行为适配。

## 许可证

项目自有代码、文档和独立资源采用 Apache License 2.0。第三方产品名称和包名仅用于兼容性说明，不授予商标权。
