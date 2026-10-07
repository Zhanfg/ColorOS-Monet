package dev.axymorrsen.colorosartplus;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.drawable.AdaptiveIconDrawable;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import android.os.Build;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

final class ArtPlusGenerator {
    static final int SIZE_1X1 = 240;
    static final int SIZE_1X2_W = 240;
    static final int SIZE_1X2_H = 820;
    static final int SIZE_2X1_W = 820;
    static final int SIZE_2X1_H = 240;
    static final int SIZE_2X2 = 704;

    interface Listener {
        void onMessage(String message);
    }

    static final class Summary {
        int generated;
        int adaptive;
        int conservative;
        int failed;
    }

    private static final class Layers {
        final Bitmap recfg;
        final Bitmap recbg;
        final Bitmap nativeMono;
        final boolean adaptive;
        final boolean conservative;

        Layers(Bitmap recfg, Bitmap recbg, Bitmap nativeMono, boolean adaptive, boolean conservative) {
            this.recfg = recfg;
            this.recbg = recbg;
            this.nativeMono = nativeMono;
            this.adaptive = adaptive;
            this.conservative = conservative;
        }
    }

    private final Context context;
    private final PackageManager pm;
    private final File outputRoot;

    ArtPlusGenerator(Context context, File outputRoot) {
        this.context = context.getApplicationContext();
        this.pm = this.context.getPackageManager();
        this.outputRoot = outputRoot;
    }

    Summary generateAll(Listener listener) {
        deleteRecursively(outputRoot);
        if (!outputRoot.mkdirs() && !outputRoot.isDirectory()) {
            throw new IllegalStateException("无法创建输出目录 " + outputRoot);
        }

        Intent launcher = new Intent(Intent.ACTION_MAIN);
        launcher.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> entries = pm.queryIntentActivities(launcher, 0);
        Set<String> seen = new HashSet<>();
        Summary summary = new Summary();

        for (ResolveInfo ri : entries) {
            if (ri.activityInfo == null || ri.activityInfo.packageName == null) continue;
            String pkg = ri.activityInfo.packageName;
            if (pkg.equals(context.getPackageName()) || !seen.add(pkg)) continue;

            try {
                Drawable icon = ri.loadIcon(pm);
                if (icon == null) throw new IllegalStateException("图标为空");
                Layers layers = buildLayers(icon);
                File dir = new File(outputRoot, pkg);
                if (!dir.mkdirs() && !dir.isDirectory()) {
                    throw new IllegalStateException("无法创建 " + dir);
                }
                writePackage(dir, layers);
                summary.generated++;
                if (layers.adaptive) summary.adaptive++;
                if (layers.conservative) summary.conservative++;
                listener.onMessage("✓ " + pkg + (layers.adaptive ? " [Adaptive]" : layers.conservative ? " [保守]" : " [Legacy]"));
            } catch (Throwable t) {
                summary.failed++;
                listener.onMessage("✗ " + pkg + " · " + t.getClass().getSimpleName());
            }
        }
        return summary;
    }

    private Layers buildLayers(Drawable icon) {
        if (Build.VERSION.SDK_INT >= 26 && icon instanceof AdaptiveIconDrawable) {
            AdaptiveIconDrawable adaptive = (AdaptiveIconDrawable) icon;
            Drawable bgDrawable = adaptive.getBackground();
            Drawable fgDrawable = adaptive.getForeground();
            if (bgDrawable == null) bgDrawable = new ColorDrawable(Color.TRANSPARENT);
            Bitmap bg = drawDrawable(bgDrawable, SIZE_1X1, SIZE_1X1, false);
            Bitmap fg = drawDrawable(fgDrawable, SIZE_1X1, SIZE_1X1, true);
            Bitmap mono = null;
            if (Build.VERSION.SDK_INT >= 33) {
                Drawable md = adaptive.getMonochrome();
                if (md != null) mono = drawDrawable(md, SIZE_1X1, SIZE_1X1, true);
            }
            return new Layers(fg, bg, mono, true, false);
        }

        Bitmap source = drawDrawable(icon, SIZE_1X1, SIZE_1X1, true);
        return splitLegacy(source);
    }

    private Layers splitLegacy(Bitmap source) {
        EdgeModel edge = estimateEdge(source);
        if (edge.opaqueRatio < 0.35 || edge.confidence < 0.68) {
            return new Layers(source, transparentBitmap(SIZE_1X1, SIZE_1X1), null, false, true);
        }

        Bitmap bg = solidBitmap(SIZE_1X1, SIZE_1X1, edge.color);
        Bitmap fg = subtractBackground(source, edge.color);
        double coverage = alphaCoverage(fg);
        if (coverage < 0.045 || coverage > 0.84 || touchesEveryEdge(fg)) {
            return new Layers(source, transparentBitmap(SIZE_1X1, SIZE_1X1), null, false, true);
        }
        return new Layers(fg, bg, null, false, false);
    }

    private void writePackage(File dir, Layers layers) throws Exception {
        Bitmap night = createNightForeground(layers.recfg, layers.recbg);
        Bitmap monoDark = layers.nativeMono != null
                ? normalizeMono(layers.nativeMono, false)
                : createMonochrome(layers.recfg, false);
        Bitmap monoLight = layers.nativeMono != null
                ? normalizeMono(layers.nativeMono, true)
                : createMonochrome(layers.recfg, true);

        savePng(layers.recbg, new File(dir, "recbg.png"));
        savePng(layers.recfg, new File(dir, "recfg.png"));
        savePng(night, new File(dir, "rec_night.png"));
        savePng(monoDark, new File(dir, "monochrome.png"));
        savePng(monoLight, new File(dir, "monochrome_light.png"));
        savePng(monoDark, new File(dir, "monochrome_dark.png"));

        savePng(scaleTo(layers.recbg, SIZE_1X2_W, SIZE_1X2_H), new File(dir, "recbg_1x2.png"));
        savePng(scaleTo(layers.recbg, SIZE_2X1_W, SIZE_2X1_H), new File(dir, "recbg_2x1.png"));
        savePng(scaleTo(layers.recbg, SIZE_2X2, SIZE_2X2), new File(dir, "recbg_2x2.png"));

        savePng(centerOnCanvas(layers.recfg, SIZE_1X2_W, SIZE_1X2_H), new File(dir, "recfg_1x2.png"));
        savePng(centerOnCanvas(layers.recfg, SIZE_2X1_W, SIZE_2X1_H), new File(dir, "recfg_2x1.png"));
        savePng(centerOnCanvas(layers.recfg, SIZE_2X2, SIZE_2X2), new File(dir, "recfg_2x2.png"));

        savePng(centerOnCanvas(night, SIZE_1X2_W, SIZE_1X2_H), new File(dir, "rec_night_1x2.png"));
        savePng(centerOnCanvas(night, SIZE_2X1_W, SIZE_2X1_H), new File(dir, "rec_night_2x1.png"));
        savePng(centerOnCanvas(night, SIZE_2X2, SIZE_2X2), new File(dir, "rec_night_2x2.png"));

        savePng(centerOnCanvas(monoDark, SIZE_1X2_W, SIZE_1X2_H), new File(dir, "monochrome_1x2.png"));
        savePng(centerOnCanvas(monoDark, SIZE_2X1_W, SIZE_2X1_H), new File(dir, "monochrome_2x1.png"));
        savePng(centerOnCanvas(monoDark, SIZE_2X2, SIZE_2X2), new File(dir, "monochrome_2x2.png"));
    }

    void installAllWithRoot() throws Exception {
        String src = shellQuote(outputRoot.getAbsolutePath());
        String cmd =
                "set -e; src=" + src + "; backup=/data/adb/coloros-monet/artplus-backup/original; " +
                "mkdir -p \"$backup\"; chmod 0700 /data/adb/coloros-monet /data/adb/coloros-monet/artplus-backup \"$backup\" 2>/dev/null || true; " +
                "for dir in \"$src\"/*; do " +
                "[ -d \"$dir\" ] || continue; pkg=$(basename \"$dir\"); dst=/data/oplus/uxicons/\"$pkg\"; bak=\"$backup/$pkg\"; " +
                "if [ -d \"$dst\" ] && [ ! -e \"$bak/.captured\" ]; then " +
                "mkdir -p \"$bak\"; cp -a \"$dst\"/. \"$bak\"/ 2>/dev/null || true; touch \"$bak/.captured\"; " +
                "fi; " +
                "mkdir -p \"$dst\"; cp -f \"$dir\"/*.png \"$dst\"/; chmod 0644 \"$dst\"/*.png; " +
                "restorecon -RF \"$dst\" 2>/dev/null || true; " +
                "done";
        runRoot(cmd);
    }

    void restoreOriginalsWithRoot() throws Exception {
        String cmd =
                "set -e; backup=/data/adb/coloros-monet/artplus-backup/original; " +
                "[ -d \"$backup\" ] || exit 0; " +
                "for bak in \"$backup\"/*; do " +
                "[ -d \"$bak\" ] || continue; pkg=$(basename \"$bak\"); dst=/data/oplus/uxicons/\"$pkg\"; " +
                "rm -rf \"$dst\"; mkdir -p \"$dst\"; " +
                "find \"$bak\" -maxdepth 1 -type f ! -name .captured -exec cp -f {} \"$dst\"/ \\;; " +
                "if ! find \"$dst\" -maxdepth 1 -type f | grep -q .; then rmdir \"$dst\" 2>/dev/null || true; " +
                "else chmod 0644 \"$dst\"/* 2>/dev/null || true; restorecon -RF \"$dst\" 2>/dev/null || true; fi; " +
                "done";
        runRoot(cmd);
    }

    void refreshLauncher() throws Exception {
        runRoot("am force-stop com.android.launcher; input keyevent KEYCODE_HOME");
    }

    static boolean hasRoot() {
        try {
            return runRoot("id -u").trim().equals("0");
        } catch (Throwable ignored) {
            return false;
        }
    }

    private static String runRoot(String command) throws Exception {
        Process process = new ProcessBuilder("su", "-c", command).redirectErrorStream(true).start();
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        StringBuilder out = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) out.append(line).append('\n');
        int rc = process.waitFor();
        if (rc != 0) throw new IllegalStateException("su 退出码 " + rc + ": " + out);
        return out.toString();
    }

    private static String shellQuote(String raw) {
        return "'" + raw.replace("'", "'\\''") + "'";
    }

    private static Bitmap drawDrawable(Drawable drawable, int width, int height, boolean transparent) {
        Bitmap out = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(out);
        if (!transparent) canvas.drawColor(Color.TRANSPARENT);
        int oldL = drawable.getBounds().left;
        int oldT = drawable.getBounds().top;
        int oldR = drawable.getBounds().right;
        int oldB = drawable.getBounds().bottom;
        drawable.setBounds(0, 0, width, height);
        drawable.draw(canvas);
        drawable.setBounds(oldL, oldT, oldR, oldB);
        return out;
    }

    private static Bitmap transparentBitmap(int w, int h) {
        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
    }

    private static Bitmap solidBitmap(int w, int h, int color) {
        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        new Canvas(out).drawColor(Color.rgb(Color.red(color), Color.green(color), Color.blue(color)));
        return out;
    }

    private static Bitmap scaleTo(Bitmap source, int w, int h) {
        return Bitmap.createScaledBitmap(source, w, h, true);
    }

    private static Bitmap centerOnCanvas(Bitmap source, int w, int h) {
        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(out);
        float x = (w - source.getWidth()) * 0.5f;
        float y = (h - source.getHeight()) * 0.5f;
        canvas.drawBitmap(source, x, y, null);
        return out;
    }

    private static void savePng(Bitmap bitmap, File file) throws Exception {
        try (FileOutputStream out = new FileOutputStream(file)) {
            if (!bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)) {
                throw new IllegalStateException("PNG 编码失败: " + file.getName());
            }
        }
    }

    private static Bitmap subtractBackground(Bitmap source, int bgColor) {
        int w = source.getWidth(), h = source.getHeight();
        int[] src = new int[w * h];
        int[] dst = new int[src.length];
        source.getPixels(src, 0, w, 0, 0, w, h);
        double[] bg = okLab(bgColor);

        for (int i = 0; i < src.length; i++) {
            int p = src[i];
            int sa = Color.alpha(p);
            if (sa <= 3) {
                dst[i] = Color.TRANSPARENT;
                continue;
            }
            double d = deltaE(okLab(p), bg);
            double a = smoothstep(0.025, 0.18, d);
            int oa = clamp255((int) Math.round(sa * a));
            if (oa <= 5) {
                dst[i] = Color.TRANSPARENT;
                continue;
            }
            double fa = Math.max(0.02, a);
            int r = uncomposite(Color.red(p), Color.red(bgColor), fa);
            int g = uncomposite(Color.green(p), Color.green(bgColor), fa);
            int b = uncomposite(Color.blue(p), Color.blue(bgColor), fa);
            dst[i] = Color.argb(oa, r, g, b);
        }

        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        out.setPixels(dst, 0, w, 0, 0, w, h);
        return out;
    }

    private static int uncomposite(int visible, int bg, double alpha) {
        return clamp255((int) Math.round((visible - (1.0 - alpha) * bg) / alpha));
    }

    private static Bitmap createNightForeground(Bitmap source, Bitmap background) {
        int w = source.getWidth(), h = source.getHeight();
        int[] src = new int[w * h];
        int[] dst = new int[src.length];
        source.getPixels(src, 0, w, 0, 0, w, h);
        double bgL = meanLabLightness(background);

        for (int i = 0; i < src.length; i++) {
            int p = src[i];
            int alpha = Color.alpha(p);
            if (alpha == 0) {
                dst[i] = Color.TRANSPARENT;
                continue;
            }
            double[] lab = okLab(p);
            double chroma = Math.hypot(lab[1], lab[2]);

            if (bgL < 0.55) {
                if (chroma < 0.045 && lab[0] < 0.50) {
                    lab[0] = Math.max(lab[0], 0.78);
                } else if (lab[0] < 0.46) {
                    lab[0] = Math.max(lab[0], 0.62);
                } else if (lab[0] < 0.60) {
                    lab[0] = lab[0] + (0.62 - lab[0]) * 0.45;
                }
            } else if (lab[0] < 0.20 && chroma < 0.035) {
                lab[0] = 0.30;
            }

            if (chroma > 0.30) {
                double scale = 0.30 / chroma;
                lab[1] *= scale;
                lab[2] *= scale;
            }
            dst[i] = colorFromOkLab(alpha, lab[0], lab[1], lab[2]);
        }

        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        out.setPixels(dst, 0, w, 0, 0, w, h);
        return out;
    }

    private static Bitmap normalizeMono(Bitmap source, boolean invert) {
        return createMonochrome(source, invert);
    }

    private static Bitmap createMonochrome(Bitmap source, boolean invert) {
        int w = source.getWidth(), h = source.getHeight();
        int[] src = new int[w * h];
        int[] dst = new int[src.length];
        source.getPixels(src, 0, w, 0, 0, w, h);

        int min = 255, max = 0;
        int visible = 0;
        for (int p : src) {
            if (Color.alpha(p) <= 8) continue;
            int y = luma8(p);
            min = Math.min(min, y);
            max = Math.max(max, y);
            visible++;
        }

        boolean flat = visible == 0 || max - min < 28;
        for (int i = 0; i < src.length; i++) {
            int p = src[i];
            int a = Color.alpha(p);
            if (a <= 0) {
                dst[i] = Color.TRANSPARENT;
                continue;
            }
            double tonal;
            if (flat) {
                tonal = 1.0;
            } else {
                double n = (luma8(p) - min) / (double) (max - min);
                tonal = invert ? 1.0 - n : n;
                tonal = 0.18 + 0.82 * tonal;
            }
            int oa = clamp255((int) Math.round(a * tonal));
            dst[i] = Color.argb(oa, 255, 255, 255);
        }

        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        out.setPixels(dst, 0, w, 0, 0, w, h);
        return out;
    }

    private static int luma8(int p) {
        return clamp255((int) Math.round(
                0.2126 * Color.red(p) + 0.7152 * Color.green(p) + 0.0722 * Color.blue(p)));
    }

    private static double meanLabLightness(Bitmap bitmap) {
        int w = bitmap.getWidth(), h = bitmap.getHeight();
        int[] pixels = new int[w * h];
        bitmap.getPixels(pixels, 0, w, 0, 0, w, h);
        double sum = 0;
        double weight = 0;
        for (int p : pixels) {
            int a = Color.alpha(p);
            if (a <= 8) continue;
            double wa = a / 255.0;
            sum += okLab(p)[0] * wa;
            weight += wa;
        }
        return weight > 0 ? sum / weight : 0.25;
    }

    private static final class EdgeModel {
        final int color;
        final double opaqueRatio;
        final double confidence;

        EdgeModel(int color, double opaqueRatio, double confidence) {
            this.color = color;
            this.opaqueRatio = opaqueRatio;
            this.confidence = confidence;
        }
    }

    private static EdgeModel estimateEdge(Bitmap source) {
        int w = source.getWidth(), h = source.getHeight();
        int band = Math.max(4, Math.round(Math.min(w, h) * 0.08f));
        List<Integer> rs = new ArrayList<>();
        List<Integer> gs = new ArrayList<>();
        List<Integer> bs = new ArrayList<>();
        int total = 0;
        int opaque = 0;

        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                if (!(x < band || y < band || x >= w - band || y >= h - band)) continue;
                total++;
                int p = source.getPixel(x, y);
                if (Color.alpha(p) < 220) continue;
                opaque++;
                rs.add(Color.red(p));
                gs.add(Color.green(p));
                bs.add(Color.blue(p));
            }
        }

        if (opaque == 0) return new EdgeModel(Color.TRANSPARENT, 0.0, 0.0);
        Collections.sort(rs);
        Collections.sort(gs);
        Collections.sort(bs);
        int mid = opaque / 2;
        int color = Color.rgb(rs.get(mid), gs.get(mid), bs.get(mid));
        double[] center = okLab(color);
        double sum = 0;
        int samples = 0;
        for (int y = 0; y < h; y += 2) {
            for (int x = 0; x < w; x += 2) {
                if (!(x < band || y < band || x >= w - band || y >= h - band)) continue;
                int p = source.getPixel(x, y);
                if (Color.alpha(p) < 220) continue;
                sum += deltaE(okLab(p), center);
                samples++;
            }
        }
        double deviation = samples == 0 ? 1.0 : sum / samples;
        double opaqueRatio = total == 0 ? 0.0 : opaque / (double) total;
        double uniformity = clamp01(1.0 - deviation / 0.16);
        double confidence = clamp01(opaqueRatio * 0.55 + uniformity * 0.45);
        return new EdgeModel(color, opaqueRatio, confidence);
    }

    private static double alphaCoverage(Bitmap source) {
        int w = source.getWidth(), h = source.getHeight();
        int[] pixels = new int[w * h];
        source.getPixels(pixels, 0, w, 0, 0, w, h);
        int count = 0;
        for (int p : pixels) if (Color.alpha(p) > 20) count++;
        return count / (double) pixels.length;
    }

    private static boolean touchesEveryEdge(Bitmap source) {
        int w = source.getWidth(), h = source.getHeight();
        boolean top = false, bottom = false, left = false, right = false;
        for (int x = 0; x < w; x++) {
            top |= Color.alpha(source.getPixel(x, 0)) > 20;
            bottom |= Color.alpha(source.getPixel(x, h - 1)) > 20;
        }
        for (int y = 0; y < h; y++) {
            left |= Color.alpha(source.getPixel(0, y)) > 20;
            right |= Color.alpha(source.getPixel(w - 1, y)) > 20;
        }
        return top && bottom && left && right;
    }

    private static double smoothstep(double a, double b, double x) {
        double t = clamp01((x - a) / (b - a));
        return t * t * (3.0 - 2.0 * t);
    }

    private static double deltaE(double[] a, double[] b) {
        double d0 = a[0] - b[0], d1 = a[1] - b[1], d2 = a[2] - b[2];
        return Math.sqrt(d0 * d0 + d1 * d1 + d2 * d2);
    }

    private static double[] okLab(int color) {
        double r = srgbToLinear(Color.red(color) / 255.0);
        double g = srgbToLinear(Color.green(color) / 255.0);
        double b = srgbToLinear(Color.blue(color) / 255.0);

        double l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b;
        double m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b;
        double s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b;

        double lp = Math.cbrt(l);
        double mp = Math.cbrt(m);
        double sp = Math.cbrt(s);

        return new double[]{
                0.2104542553 * lp + 0.7936177850 * mp - 0.0040720468 * sp,
                1.9779984951 * lp - 2.4285922050 * mp + 0.4505937099 * sp,
                0.0259040371 * lp + 0.7827717662 * mp - 0.8086757660 * sp
        };
    }

    private static int colorFromOkLab(int alpha, double L, double A, double B) {
        double lp = L + 0.3963377774 * A + 0.2158037573 * B;
        double mp = L - 0.1055613458 * A - 0.0638541728 * B;
        double sp = L - 0.0894841775 * A - 1.2914855480 * B;
        double l = lp * lp * lp;
        double m = mp * mp * mp;
        double s = sp * sp * sp;

        double r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
        double g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
        double b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s;

        return Color.argb(
                clamp255(alpha),
                clamp255((int) Math.round(linearToSrgb(r) * 255.0)),
                clamp255((int) Math.round(linearToSrgb(g) * 255.0)),
                clamp255((int) Math.round(linearToSrgb(b) * 255.0))
        );
    }

    private static double srgbToLinear(double c) {
        c = clamp01(c);
        return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    }

    private static double linearToSrgb(double c) {
        c = clamp01(c);
        return c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1.0 / 2.4) - 0.055;
    }

    private static int clamp255(int v) {
        return Math.max(0, Math.min(255, v));
    }

    private static double clamp01(double v) {
        return Math.max(0.0, Math.min(1.0, v));
    }

    private static void deleteRecursively(File file) {
        if (!file.exists()) return;
        if (file.isDirectory()) {
            File[] children = file.listFiles();
            if (children != null) for (File child : children) deleteRecursively(child);
        }
        //noinspection ResultOfMethodCallIgnored
        file.delete();
    }
}
