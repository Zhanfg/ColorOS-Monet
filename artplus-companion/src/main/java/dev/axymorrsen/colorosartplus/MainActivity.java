package dev.axymorrsen.colorosartplus;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.File;

public final class MainActivity extends Activity {
    private TextView status;
    private Button generate;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        int pad = Math.round(20 * getResources().getDisplayMetrics().density);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(pad, pad, pad, pad);

        TextView title = new TextView(this);
        title.setText("ColorOS 17 · ART+ Auto");
        title.setTextSize(24f);
        root.addView(title);

        TextView desc = new TextView(this);
        desc.setText("Adaptive Icon 直接保留原生前景/背景层；旧式图标仅在高置信度时自动拆层。生成 recfg / recbg / rec_night / monochrome 后写入 /data/oplus/uxicons。");
        desc.setTextSize(15f);
        desc.setPadding(0, pad / 2, 0, pad);
        root.addView(desc);

        generate = new Button(this);
        generate.setText("一键生成并应用");
        root.addView(generate);

        status = new TextView(this);
        status.setText("尚未运行。");
        status.setTextIsSelectable(true);
        status.setPadding(0, pad, 0, pad);
        root.addView(status);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(root);
        setContentView(scroll);

        generate.setOnClickListener(v -> runGeneration());
    }

    private void runGeneration() {
        generate.setEnabled(false);
        status.setText("正在请求 Root 并扫描桌面应用……");
        new Thread(() -> {
            StringBuilder log = new StringBuilder();
            try {
                if (!ArtPlusGenerator.hasRoot()) {
                    throw new IllegalStateException("未获得 Root 权限。");
                }
                File out = new File(getFilesDir(), "artplus-generated");
                ArtPlusGenerator generator = new ArtPlusGenerator(this, out);
                ArtPlusGenerator.Summary summary = generator.generateAll(message -> {
                    synchronized (log) {
                        log.append(message).append('\n');
                    }
                    runOnUiThread(() -> status.setText(log.toString()));
                });
                generator.installAllWithRoot();
                generator.refreshLauncher();
                synchronized (log) {
                    log.append("\n完成：")
                        .append(summary.generated)
                        .append(" 个；原生分层 ")
                        .append(summary.adaptive)
                        .append(" 个；保守回退 ")
                        .append(summary.conservative)
                        .append(" 个；失败 ")
                        .append(summary.failed)
                        .append(" 个。");
                }
            } catch (Throwable t) {
                synchronized (log) {
                    log.append("\n失败：").append(t.getClass().getSimpleName())
                        .append(": ").append(t.getMessage());
                }
            }
            runOnUiThread(() -> {
                status.setText(log.toString());
                generate.setEnabled(true);
            });
        }, "ArtPlusAuto").start();
    }
}
