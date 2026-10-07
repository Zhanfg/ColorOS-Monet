package dev.zhanfg.colorosmonet.bridge.ui;

import android.app.Activity;\nimport android.app.AlertDialog;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;

import dev.zhanfg.colorosmonet.bridge.artplus.ArtPlusGenerator;

public final class GeneratorActivity extends Activity {
    private TextView status;
    private ProgressBar progress;
    private Button scanButton;
    private Button generateButton;
    private CheckBox refreshLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTitle("ColorOS 17 ART+ Generator");

        int pad = Math.round(20 * getResources().getDisplayMetrics().density);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(pad, pad, pad, pad);

        TextView title = new TextView(this);
        title.setText("ColorOS 17 ART+ 自动图标生成器");
        title.setTextSize(23);
        title.setGravity(Gravity.START);
        content.addView(title, matchWrap());

        TextView desc = new TextView(this);
        desc.setText("优先读取 Adaptive Icon 原生前景 / 背景 / monochrome；只有旧式单层图标才执行本地分层。生成结果写入 /data/oplus/uxicons/{package}。\n\n生成器版本：" + ArtPlusGenerator.GENERATOR_VERSION);
        desc.setTextSize(15);
        desc.setPadding(0, pad / 2, 0, pad);
        content.addView(desc, matchWrap());

        scanButton = new Button(this);
        scanButton.setText("扫描应用");
        content.addView(scanButton, matchWrap());

        generateButton = new Button(this);
        generateButton.setText("一键补全缺失暗色图标");
        content.addView(generateButton, matchWrap());

        restoreButton = new Button(this);
        restoreButton.setText("恢复上次生成前状态");
        content.addView(restoreButton, matchWrap());

        refreshLauncher = new CheckBox(this);
        refreshLauncher.setText("完成后刷新桌面缓存（会短暂重载桌面）");
        refreshLauncher.setChecked(true);
        content.addView(refreshLauncher, matchWrap());

        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        progress.setVisibility(View.GONE);
        content.addView(progress, matchWrap());

        status = new TextView(this);
        status.setText("状态：未扫描");
        status.setTextSize(14);
        status.setPadding(0, pad, 0, pad);
        content.addView(status, matchWrap());

        ScrollView scroll = new ScrollView(this);
        scroll.addView(content);
        setContentView(scroll);

        scanButton.setOnClickListener(v -> runScan());
        generateButton.setOnClickListener(v -> runGenerate());
        restoreButton.setOnClickListener(v -> confirmRestore());
    }

    private LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
    }

    private void setBusy(boolean busy) {
        scanButton.setEnabled(!busy);
        generateButton.setEnabled(!busy);
        restoreButton.setEnabled(!busy);
        progress.setVisibility(busy ? View.VISIBLE : View.GONE);
    }

    private void runScan() {
        setBusy(true);
        status.setText("状态：正在扫描…");
        new Thread(() -> {
            try {
                ArtPlusGenerator.ScanSummary summary = ArtPlusGenerator.scan(this);
                runOnUiThread(() -> {
                    status.setText("扫描完成：" + summary.asText());
                    setBusy(false);
                });
            } catch (Throwable t) {
                failUi(t);
            }
        }, "artplus-scan").start();
    }

    private void runGenerate() {
        if (!ArtPlusGenerator.hasRoot()) {
            status.setText("无法开始：没有获得 root。请在 Root 管理器中允许本应用。");
            return;
        }
        setBusy(true);
        progress.setProgress(0);
        status.setText("状态：准备生成…");
        final boolean doRefresh = refreshLauncher.isChecked();
        new Thread(() -> {
            try {
                ArtPlusGenerator.Summary summary = ArtPlusGenerator.generateAll(this, (done, total, pkg, state) -> {
                    int pct = total == 0 ? 0 : Math.round(done * 100f / total);
                    runOnUiThread(() -> {
                        progress.setProgress(pct);
                        status.setText(state + "  " + pkg + "\n" + done + " / " + total);
                    });
                });
                String refreshState = "";
                if (doRefresh) {
                    try {
                        ArtPlusGenerator.refreshLauncherWithRoot();
                        refreshState = "\n桌面缓存：已请求刷新";
                    } catch (Throwable t) {
                        refreshState = "\n桌面缓存：刷新失败，但图标文件已经写入";
                    }
                }
                final String tail = refreshState;
                runOnUiThread(() -> {
                    progress.setProgress(100);
                    StringBuilder text = new StringBuilder("完成：").append(summary.asText()).append(tail);
                    if (!summary.failures.isEmpty()) {
                        text.append("\n\n失败项（最多显示 12 个）：");
                        for (int i = 0; i < Math.min(12, summary.failures.size()); i++) {
                            text.append("\n• ").append(summary.failures.get(i));
                        }
                    }
                    status.setText(text.toString());
                    setBusy(false);
                });
            } catch (Throwable t) {
                failUi(t);
            }
        }, "artplus-generate").start();
    }

    private void confirmRestore() {
        if (!ArtPlusGenerator.hasRoot()) {
            status.setText("无法恢复：没有获得 root。");
            return;
        }
        new AlertDialog.Builder(this)
                .setTitle("恢复上次生成前状态")
                .setMessage("只恢复本工具上一次批量生成触碰过的 /data/oplus/uxicons 包目录。系统内置 /my_product 资源不会被修改。")
                .setNegativeButton("取消", null)
                .setPositiveButton("恢复", (dialog, which) -> runRestore())
                .show();
    }

    private void runRestore() {
        setBusy(true);
        status.setText("状态：正在恢复上次备份…");
        new Thread(() -> {
            try {
                ArtPlusGenerator.restoreLastBackupWithRoot();
                try {
                    ArtPlusGenerator.refreshLauncherWithRoot();
                } catch (Throwable ignored) {
                }
                runOnUiThread(() -> {
                    status.setText("恢复完成。已还原上次生成触碰过的 data 层 ART+ 目录。");
                    setBusy(false);
                });
            } catch (Throwable t) {
                failUi(t);
            }
        }, "artplus-restore").start();
    }

    private void failUi(Throwable t) {
        runOnUiThread(() -> {
            String message = t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage();
            status.setText("失败：" + message);
            setBusy(false);
        });
    }
}
