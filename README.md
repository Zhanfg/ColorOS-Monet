# ColorOS Monet

ColorOS Monet 是一个面向 ColorOS、OxygenOS 及常用 Android 应用的动态配色与界面组件系统。

当前架构明确分为两层：

- **COE APK 前端**：项目所有者提供的 `one.dot.couiexpressive` 作为用户实际操作界面，并保留其自身可选的 LSPosed 行为层。
- **Rust / CMONET01 后端**：`monetctl` 管理组件、校验、FRRO 资源覆盖、状态和壁纸色变化后的重应用。

详细前端边界见 [`docs/FRONTEND_COE.md`](docs/FRONTEND_COE.md)。

## 为什么不再做独立 WebUI

此前分支把 COE 2.5 仅作为视觉/能力参考，并计划另做 WebUI。现在需求已经调整：**COE 2.5 APK 本身就是前端**，因此模块 Action 直接打开 COE，而不是继续维护一套重复的 WebUI。

公开仓库仍不会提交用户提供的 COE APK 二进制。`tools/package_module.py` 支持在本地或私有构建阶段使用 `--frontend-apk` 注入该 APK。

## 后端

后端继续保持：

- **Rust `monetctl`**：组件校验、安装、启停、应用和监听。
- **`.cmonet` 组件包**：固定 `CMONET01` 文件头、Manifest SHA-256 和 Payload SHA-256。
- **Fabricated Runtime Resource Overlay（FRRO）**：动态注册资源，不再给每个目标分发独立 Overlay APK。
- **`SKIPMOUNT=true`**：模块本身不通过 `/system`、`/product`、`system_ext` 或 `/vendor` 静态挂载实现资源覆盖。

COE 前端 APK 是唯一允许在私有整合包中出现的 APK；其他 APK 载荷仍被安装器拒绝。

## 已重新实现的资源组件

当前后端包含 40 个 `.cmonet` 组件，覆盖：

- ColorOS / OPlus / OnePlus：设置、SystemUI、无线设置、桌面、电话、联系人、时钟、相机、电池、权限、安全中心、通知管理、Breeno、儿童空间、护眼、OShare 等；
- Scene；
- 微信及多个微信界面变体；
- X、TIM、酷安。

资源组件与 COE 行为 Hook 是两个不同层级。布局重构、手势、动画、锁屏结构、音量面板行为等不是 FRRO 能力，不能因为资源组件成功打包就宣称等价实现。

## COE 前端整合

用户提供的 COE 2.5 APK 静态识别结果：

```text
package: one.dot.couiexpressive
settings activity: one.dot.couiexpressive.ui.SettingsActivity
launcher alias: one.dot.couiexpressive.LauncherActivityAlias
xposed entry: one.dot.couiexpressive.hooks.HookEntry
```

私有整合构建：

```bash
python tools/package_module.py \
  --runtime runtime/target/aarch64-linux-android/release/monetctl \
  --components build/components \
  --frontend-apk '/path/to/COE 2.5.apk' \
  --version dev-26-coe-frontend \
  --version-code 26 \
  --output dist/ColorOS-Monet-dev-26.zip
```

开机完成后，模块会通过 Package Manager 安装或更新前端；若设备已有 COE 且签名/版本不允许替换，则保留现有安装并记录日志。**不会自动启用 LSPosed Scope。**

模块 Action 现在直接打开 COE 设置界面。

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

## 设备端后端管理

```sh
/data/adb/modules/coloros_monet/bin/monetctl list
/data/adb/modules/coloros_monet/bin/monetctl enable tim-monet
/data/adb/modules/coloros_monet/bin/monetctl disable tim-monet
/data/adb/modules/coloros_monet/bin/monetctl apply-all
```

运行状态位于：

```text
/data/adb/coloros-monet/
```

前端安装结果：

```text
/data/adb/coloros-monet/frontend.status
/data/adb/coloros-monet/runtime/frontend-install.log
```

## 兼容性

FRRO 仍受目标应用 `overlayable`、签名、actor 和 OEM OverlayManager 策略约束。COE 自身的 Hook 也受 LSPosed Scope、ColorOS 版本和目标类结构影响。

因此当前整合包仍属于设备集成测试版本，必须在一加 13 / ColorOS 16 上验证：

- COE 安装、打开、升级与现有安装冲突；
- LSPosed Scope 手动启用后的 SystemUI/Launcher 稳定性；
- CMONET 资源覆盖接受情况；
- COE Hook 与 FRRO 是否存在重复修改；
- 禁用、回滚和卸载路径。

## 许可证与二进制边界

项目自有代码、文档和独立资源采用 Apache License 2.0。用户提供的 COE APK 是外部二进制，不因被私有整合包引用而自动变成项目自有代码，也不会被提交到公开仓库。
