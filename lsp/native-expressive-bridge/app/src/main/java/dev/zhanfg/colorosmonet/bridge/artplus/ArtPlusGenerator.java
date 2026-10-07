package dev.zhanfg.colorosmonet.bridge.artplus;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.PorterDuff;
import android.graphics.Rect;
import android.graphics.drawable.AdaptiveIconDrawable;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import android.os.Build;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Offline compiler for the ColorOS 17 ART+ icon contract.
 *
 * ColorOS Launcher 17.3.12 checks /data/oplus/uxicons before the built-in
 * /my_product/media/theme/uxicons tree, and selects rec_night / monochrome /
 * recfg / recbg according to its active icon mode.
 */
public final class ArtPlusGenerator {
    public static final String GENERATOR_VERSION = "0.2.1-alpha1";

    private static final int S = 240;
    private static final int S2 = 704;
    private static final int LONG = 820;
    private static final int VISIBLE_ALPHA = 8;
    private static final double SAFE_CONFIDENCE = 0.62;
    private static final String ROOT_UXICONS = "/data/oplus/uxicons";

    private ArtPlusGenerator() {}

    public interface ProgressCallback {
        void onProgress(int done, int total, String packageName, String state);
    }

    public static final class ScanSummary {
        public int total;
        public int adaptive;
        public int legacy;

        public String asText() {
            return "可启动应用 " + total + " · Adaptive " + adaptive + " · Legacy " + legacy;
        }
    }

    public static final class Summary {
        public int total;
        public int generated;
        public int adaptive;
        public int legacySeparated;
        public int legacyConservative;
        public int failed;
        public final List<String> failures = new ArrayList<>();

        public String asText() {
            return "总计 " + total
                    + " · 已生成 " + generated
                    + " · Adaptive " + adaptive
                    + " · Legacy 分层 " + legacySeparated
                    + " · 保守回退 " + legacyConservative
                    + " · 失败 " + failed;
        }
    }

    private static final class Layers {
        Bitmap recfg;
        Bitmap recbg;
        Bitmap recNight;
        Bitmap monochrome;
        boolean adaptive;
        boolean conservative;
    }

    private static final class LegacyAnalysis {
        Bitmap background;
        double confidence;
    }

    public static boolean hasRoot() {
        try {
            Process p = new ProcessBuilder("su", "-c", "id -u").redirectErrorStream(true).start();
            String line;
            try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
                line = r.readLine();
            }
            return p.waitFor() == 0 && "0".equals(line == null ? "" : line.trim());
        } catch (Throwable ignored) {
            return false;
        }
    }

    public static ScanSummary scan(Context context) {
        PackageManager pm = context.getPackageManager();
        ScanSummary out = new ScanSummary();
        Set<String> seen = new HashSet<>();
        for (ResolveInfo ri : queryLauncherApps(pm)) {
            if (ri.activityInfo == null || !seen.add(ri.activityInfo.packageName)) continue;
            out.total++;
            try {
                if (ri.loadIcon(pm) instanceof AdaptiveIconDrawable) out.adaptive++;
                else out.legacy++;
            } catch (Throwable ignored) {
                out.legacy++;
            }
        }
        return out;
    }

    public static Summary generateAll(Context context, ProgressCallback callback) {
        PackageManager pm = context.getPackageManager();
        List<ResolveInfo> apps = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (ResolveInfo ri : queryLauncherApps(pm)) {
            if (ri.activityInfo != null && seen.add(ri.activityInfo.packageName)) apps.add(ri);
        }

        Summary summary = new Summary();
        summary.total = apps.size();
        int done = 0;
        for (ResolveInfo ri : apps) {
            String pkg = ri.activityInfo.packageName;
            try {
                callback.onProgress(done, summary.total, pkg, "分析");
                Layers layers = buildLayers(ri.loadIcon(pm));
                if (layers.adaptive) summary.adaptive++;
                else if (layers.conservative) summary.legacyConservative++;
                else summary.legacySeparated++;

                File stage = new File(context.getCacheDir(), "artplus_stage/" + pkg);
                recreateDir(stage);
                writePackage(stage, layers);
                callback.onProgress(done, summary.total, pkg, "写入");
                installWithRoot(stage, pkg);
                summary.generated++;
            } catch (Throwable t) {
                summary.failed++;
                summary.failures.add(pkg + ": " + t.getClass().getSimpleName() + " " + safeMessage(t));
            }
            done++;
            callback.onProgress(done, summary.total, pkg, "完成");
        }
        return summary;
    }

    public static void refreshLauncherWithRoot() throws Exception {
        runRoot("am force-stop com.android.launcher >/dev/null 2>&1 || true; "
                + "sleep 1; "
                + "am start -a android.intent.action.MAIN -c android.intent.category.HOME >/dev/null 2>&1 || true");
    }

    private static List<ResolveInfo> queryLauncherApps(PackageManager pm) {
        Intent intent = new Intent(Intent.ACTION_MAIN, null).addCategory(Intent.CATEGORY_LAUNCHER);
        return pm.queryIntentActivities(intent, PackageManager.MATCH_ALL);
    }

    private static Layers buildLayers(Drawable icon) {
        Layers out = new Layers();

        if (icon instanceof AdaptiveIconDrawable) {
            AdaptiveIconDrawable ai = (AdaptiveIconDrawable) icon;
            Drawable bg = ai.getBackground();
            if (bg == null) bg = new ColorDrawable(Color.TRANSPARENT);

            out.recbg = drawDrawable(bg, S, S, false);
            out.recfg = drawDrawable(ai.getForeground(), S, S, true);
            if (Build.VERSION.SDK_INT >= 33 && ai.getMonochrome() != null) {
                out.monochrome = normalizeNativeMonochrome(
                        drawDrawable(ai.getMonochrome(), S, S, true));
            } else {
                out.monochrome = autoMonochrome(out.recfg, out.recbg);
            }
            out.adaptive = true;
        } else {
            Bitmap source = drawDrawable(icon, S, S, true);
            LegacyAnalysis analysis = analyzeLegacy(source);
            out.recbg = analysis.background;

            if (analysis.confidence >= SAFE_CONFIDENCE) {
                Bitmap separated = separateForeground(source, analysis.background);
                double coverage = alphaCoverage(separated);
                if (coverage >= 0.015 && coverage <= 0.92) {
                    out.recfg = separated;
                } else {
                    out.recfg = source;
                    out.conservative = true;
                }
            } else {
                out.recfg = source;
                out.conservative = true;
            }
            out.monochrome = autoMonochrome(out.recfg, out.recbg);
        }

        out.recNight = makeNightForeground(out.recfg);
        return out;
    }

    private static LegacyAnalysis analyzeLegacy(Bitmap source) {
        LegacyAnalysis out = new LegacyAnalysis();
        int w = source.getWidth(), h = source.getHeight();
        int[] px = pixels(source);

        int band = Math.max(4, Math.round(Math.min(w, h) * 0.07f));
        int border = 0, opaque = 0;
        double lSum = 0, lSq = 0;
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                if (!(x < band || y < band || x >= w - band || y >= h - band)) continue;
                border++;
                int c = px[y * w + x];
                if (Color.alpha(c) > 220) {
                    opaque++;
                    double l = luma(c);
                    lSum += l;
                    lSq += l * l;
                }
            }
        }

        double opaqueRatio = border == 0 ? 0 : opaque / (double) border;
        if (opaqueRatio < 0.45) {
            out.background = solidBitmap(w, h, Color.TRANSPARENT);
            out.confidence = 0.90;
            return out;
        }

        int csz = Math.max(8, Math.round(Math.min(w, h) * 0.16f));
        int tl = medianColor(source, 0, 0, csz, csz);
        int tr = medianColor(source, w - csz, 0, w, csz);
        int bl = medianColor(source, 0, h - csz, csz, h);
        int br = medianColor(source, w - csz, h - csz, w, h);
        out.background = bilinearBackground(w, h, tl, tr, bl, br);

        double variance = 0;
        if (opaque > 0) {
            double mean = lSum / opaque;
            variance = Math.max(0, lSq / opaque - mean * mean);
        }
        double cornerSpread = Math.max(
                Math.max(colorDistance(tl, tr), colorDistance(bl, br)),
                Math.max(colorDistance(tl, bl), colorDistance(tr, br)));

        if (variance < 180 && cornerSpread < 45) out.confidence = 0.94;
        else if (variance < 650 && cornerSpread < 105) out.confidence = 0.78;
        else out.confidence = 0.48;
        return out;
    }

    private static Bitmap separateForeground(Bitmap source, Bitmap bg) {
        int w = source.getWidth(), h = source.getHeight();
        int[] sp = pixels(source), bp = pixels(bg), op = new int[sp.length];

        for (int i = 0; i < sp.length; i++) {
            int s = sp[i];
            int sa = Color.alpha(s);
            if (sa <= VISIBLE_ALPHA) continue;

            double d = colorDistance(s, bp[i]);
            double a = smoothstep(13.0, 92.0, d);
            int oa = clamp255((int) Math.round(sa * a));
            if (oa <= VISIBLE_ALPHA) continue;

            double safeA = Math.max(0.06, a);
            op[i] = Color.argb(
                    oa,
                    uncomposite(Color.red(s), Color.red(bp[i]), safeA),
                    uncomposite(Color.green(s), Color.green(bp[i]), safeA),
                    uncomposite(Color.blue(s), Color.blue(bp[i]), safeA));
        }
        return bitmapFromPixels(w, h, op);
    }

    private static Bitmap makeNightForeground(Bitmap source) {
        int w = source.getWidth(), h = source.getHeight();
        int[] sp = pixels(source), op = new int[sp.length];

        for (int i = 0; i < sp.length; i++) {
            int c = sp[i], a8 = Color.alpha(c);
            if (a8 <= 0) continue;

            double[] lab = rgbToOklab(Color.red(c), Color.green(c), Color.blue(c));
            double chroma = Math.hypot(lab[1], lab[2]);
            double L = lab[0];

            // Keep brand hue/chroma. Only lift tones that become unreadable on a dark desktop.
            double targetL = L;
            if (chroma < 0.035 && L < 0.72) targetL = 0.78 + L * 0.08;
            else if (L < 0.35) targetL = 0.56 + L * 0.25;
            else if (L < 0.50) targetL = Math.max(L, 0.58);

            // Slightly compress extreme chroma after a large lightness lift to avoid clipping.
            double lift = Math.max(0, targetL - L);
            double scale = Math.max(0.82, 1.0 - lift * 0.28);
            int[] rgb = oklabToRgb(Math.min(0.94, targetL), lab[1] * scale, lab[2] * scale);
            op[i] = Color.argb(a8, rgb[0], rgb[1], rgb[2]);
        }
        return bitmapFromPixels(w, h, op);
    }

    private static Bitmap normalizeNativeMonochrome(Bitmap source) {
        int[] sp = pixels(source), op = new int[sp.length];
        for (int i = 0; i < sp.length; i++) {
            int c = sp[i];
            int a = Color.alpha(c);
            if (a == 0) continue;
            int tonal = luma(c);
            int outA = Math.max(a, tonal);
            op[i] = Color.argb(outA, 255, 255, 255);
        }
        return bitmapFromPixels(source.getWidth(), source.getHeight(), op);
    }

    private static Bitmap autoMonochrome(Bitmap fg, Bitmap bg) {
        int w = fg.getWidth(), h = fg.getHeight();
        int[] fp = pixels(fg), bp = pixels(bg), op = new int[fp.length];

        double coverage = alphaCoverage(fg);
        boolean bakedTile = coverage > 0.84;
        int min = 255, max = 0;
        int[] raw = new int[fp.length];

        for (int i = 0; i < fp.length; i++) {
            int c = fp[i], a = Color.alpha(c);
            if (a <= VISIBLE_ALPHA) continue;
            int v;
            if (bakedTile && Color.alpha(bp[i]) > VISIBLE_ALPHA) {
                v = clamp255((int) Math.round(colorDistance(c, bp[i]) * 1.55));
            } else {
                v = luma(c);
            }
            v = clamp255((int) Math.round(v * (a / 255.0)));
            raw[i] = v;
            if (v > 0) {
                min = Math.min(min, v);
                max = Math.max(max, v);
            }
        }

        if (max <= min) {
            for (int i = 0; i < fp.length; i++) {
                int a = Color.alpha(fp[i]);
                if (a > 0) op[i] = Color.argb(a, 255, 255, 255);
            }
            return bitmapFromPixels(w, h, op);
        }

        // If edges dominate more strongly than the center, invert like AOSP's fallback.
        double edge = 0, center = 0;
        int edgeN = 0, centerN = 0;
        int band = Math.max(3, w / 10);
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                int v = raw[y * w + x];
                if (v <= 0) continue;
                if (x < band || y < band || x >= w - band || y >= h - band) {
                    edge += v; edgeN++;
                } else {
                    center += v; centerN++;
                }
            }
        }
        boolean invert = edgeN > 0 && centerN > 0 && edge / edgeN > center / centerN + 20;

        for (int i = 0; i < raw.length; i++) {
            int v = raw[i];
            if (v <= 0) continue;
            int stretched = clamp255((int) Math.round((v - min) * 255.0 / (max - min)));
            if (invert) stretched = 255 - stretched;
            int a = clamp255((int) Math.round(Math.pow(stretched / 255.0, 0.86) * 255));
            if (a > VISIBLE_ALPHA) op[i] = Color.argb(a, 255, 255, 255);
        }
        return bitmapFromPixels(w, h, op);
    }

    private static void writePackage(File dir, Layers l) throws Exception {
        savePng(l.recbg, new File(dir, "recbg.png"));
        savePng(l.recfg, new File(dir, "recfg.png"));
        savePng(l.recNight, new File(dir, "rec_night.png"));
        savePng(l.monochrome, new File(dir, "monochrome.png"));

        savePng(scaleBackground(l.recbg, S, LONG), new File(dir, "recbg_1x2.png"));
        savePng(scaleBackground(l.recbg, LONG, S), new File(dir, "recbg_2x1.png"));
        savePng(scaleBackground(l.recbg, S2, S2), new File(dir, "recbg_2x2.png"));

        savePng(centerOnCanvas(l.recfg, S, LONG), new File(dir, "recfg_1x2.png"));
        savePng(centerOnCanvas(l.recfg, LONG, S), new File(dir, "recfg_2x1.png"));
        savePng(centerOnCanvas(l.recfg, S2, S2), new File(dir, "recfg_2x2.png"));

        savePng(centerOnCanvas(l.recNight, S, LONG), new File(dir, "rec_night_1x2.png"));
        savePng(centerOnCanvas(l.recNight, LONG, S), new File(dir, "rec_night_2x1.png"));
        savePng(centerOnCanvas(l.recNight, S2, S2), new File(dir, "rec_night_2x2.png"));

        savePng(centerOnCanvas(l.monochrome, S, LONG), new File(dir, "monochrome_1x2.png"));
        savePng(centerOnCanvas(l.monochrome, LONG, S), new File(dir, "monochrome_2x1.png"));
        savePng(centerOnCanvas(l.monochrome, S2, S2), new File(dir, "monochrome_2x2.png"));
    }

    private static void installWithRoot(File source, String pkg) throws Exception {
        String src = shellQuote(source.getAbsolutePath());
        String dst = shellQuote(ROOT_UXICONS + "/" + pkg);
        runRoot("set -e; mkdir -p " + dst + "; "
                + "cp -f " + src + "/*.png " + dst + "/; "
                + "chmod 0644 " + dst + "/*.png; "
                + "restorecon -RF " + dst + " >/dev/null 2>&1 || true");
    }

    private static void runRoot(String command) throws Exception {
        Process p = new ProcessBuilder("su", "-c", command).redirectErrorStream(true).start();
        StringBuilder text = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
            String line;
            while ((line = r.readLine()) != null) text.append(line).append('\n');
        }
        int rc = p.waitFor();
        if (rc != 0) throw new IllegalStateException("root rc=" + rc + " " + text.toString().trim());
    }

    private static String shellQuote(String s) {
        return "'" + s.replace("'", "'\\''") + "'";
    }

    private static void recreateDir(File dir) {
        deleteRecursively(dir);
        if (!dir.mkdirs() && !dir.isDirectory()) throw new IllegalStateException("Cannot create " + dir);
    }

    private static void deleteRecursively(File f) {
        if (f == null || !f.exists()) return;
        if (f.isDirectory()) {
            File[] children = f.listFiles();
            if (children != null) for (File c : children) deleteRecursively(c);
        }
        //noinspection ResultOfMethodCallIgnored
        f.delete();
    }

    private static void savePng(Bitmap bitmap, File file) throws Exception {
        try (FileOutputStream out = new FileOutputStream(file)) {
            if (!bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)) {
                throw new IllegalStateException("PNG encode failed: " + file.getName());
            }
        }
    }

    private static Bitmap drawDrawable(Drawable drawable, int w, int h, boolean transparent) {
        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(out);
        if (transparent) canvas.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR);
        Rect old = new Rect(drawable.getBounds());
        drawable.setBounds(0, 0, w, h);
        drawable.draw(canvas);
        drawable.setBounds(old);
        return out;
    }

    private static Bitmap solidBitmap(int w, int h, int color) {
        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        out.eraseColor(color);
        return out;
    }

    private static Bitmap centerOnCanvas(Bitmap source, int w, int h) {
        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(out);
        c.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR);
        c.drawBitmap(source, (w - source.getWidth()) / 2f, (h - source.getHeight()) / 2f, null);
        return out;
    }

    private static Bitmap scaleBackground(Bitmap source, int w, int h) {
        if (alphaCoverage(source) < 0.05) return solidBitmap(w, h, Color.TRANSPARENT);
        return Bitmap.createScaledBitmap(source, w, h, true);
    }

    private static Bitmap bilinearBackground(int w, int h, int tl, int tr, int bl, int br) {
        int[] out = new int[w * h];
        for (int y = 0; y < h; y++) {
            double fy = h <= 1 ? 0 : y / (double) (h - 1);
            for (int x = 0; x < w; x++) {
                double fx = w <= 1 ? 0 : x / (double) (w - 1);
                int top = lerpColor(tl, tr, fx);
                int bottom = lerpColor(bl, br, fx);
                out[y * w + x] = lerpColor(top, bottom, fy);
            }
        }
        return bitmapFromPixels(w, h, out);
    }

    private static int medianColor(Bitmap src, int l, int t, int r, int b) {
        ArrayList<Integer> rs = new ArrayList<>();
        ArrayList<Integer> gs = new ArrayList<>();
        ArrayList<Integer> bs = new ArrayList<>();
        for (int y = Math.max(0, t); y < Math.min(src.getHeight(), b); y++) {
            for (int x = Math.max(0, l); x < Math.min(src.getWidth(), r); x++) {
                int c = src.getPixel(x, y);
                if (Color.alpha(c) < 180) continue;
                rs.add(Color.red(c)); gs.add(Color.green(c)); bs.add(Color.blue(c));
            }
        }
        if (rs.isEmpty()) return Color.TRANSPARENT;
        rs.sort(Integer::compareTo); gs.sort(Integer::compareTo); bs.sort(Integer::compareTo);
        int n = rs.size() / 2;
        return Color.rgb(rs.get(n), gs.get(n), bs.get(n));
    }

    private static int lerpColor(int a, int b, double t) {
        return Color.argb(
                clamp255((int) Math.round(Color.alpha(a) + (Color.alpha(b) - Color.alpha(a)) * t)),
                clamp255((int) Math.round(Color.red(a) + (Color.red(b) - Color.red(a)) * t)),
                clamp255((int) Math.round(Color.green(a) + (Color.green(b) - Color.green(a)) * t)),
                clamp255((int) Math.round(Color.blue(a) + (Color.blue(b) - Color.blue(a)) * t)));
    }

    private static int[] pixels(Bitmap b) {
        int[] px = new int[b.getWidth() * b.getHeight()];
        b.getPixels(px, 0, b.getWidth(), 0, 0, b.getWidth(), b.getHeight());
        return px;
    }

    private static Bitmap bitmapFromPixels(int w, int h, int[] px) {
        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        out.setPixels(px, 0, w, 0, 0, w, h);
        return out;
    }

    private static double alphaCoverage(Bitmap b) {
        int[] px = pixels(b);
        int visible = 0;
        for (int c : px) if (Color.alpha(c) > VISIBLE_ALPHA) visible++;
        return visible / (double) px.length;
    }

    private static double colorDistance(int a, int b) {
        double dr = Color.red(a) - Color.red(b);
        double dg = Color.green(a) - Color.green(b);
        double db = Color.blue(a) - Color.blue(b);
        return Math.sqrt(dr * dr + dg * dg + db * db);
    }

    private static double smoothstep(double lo, double hi, double x) {
        if (x <= lo) return 0;
        if (x >= hi) return 1;
        double t = (x - lo) / (hi - lo);
        return t * t * (3 - 2 * t);
    }

    private static int uncomposite(int visible, int background, double alpha) {
        return clamp255((int) Math.round((visible - (1.0 - alpha) * background) / alpha));
    }

    private static int luma(int c) {
        return clamp255((int) Math.round(
                0.2126 * Color.red(c) + 0.7152 * Color.green(c) + 0.0722 * Color.blue(c)));
    }

    private static int clamp255(int v) {
        return Math.max(0, Math.min(255, v));
    }

    private static double srgbToLinear(double c8) {
        double c = c8 / 255.0;
        return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    }

    private static double linearToSrgb(double c) {
        c = Math.max(0, Math.min(1, c));
        return c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1.0 / 2.4) - 0.055;
    }

    private static double[] rgbToOklab(int r8, int g8, int b8) {
        double r = srgbToLinear(r8), g = srgbToLinear(g8), b = srgbToLinear(b8);
        double l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b;
        double m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b;
        double s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b;
        double ll = Math.cbrt(l), mm = Math.cbrt(m), ss = Math.cbrt(s);
        return new double[] {
                0.2104542553 * ll + 0.7936177850 * mm - 0.0040720468 * ss,
                1.9779984951 * ll - 2.4285922050 * mm + 0.4505937099 * ss,
                0.0259040371 * ll + 0.7827717662 * mm - 0.8086757660 * ss
        };
    }

    private static int[] oklabToRgb(double L, double a, double b) {
        double ll = L + 0.3963377774 * a + 0.2158037573 * b;
        double mm = L - 0.1055613458 * a - 0.0638541728 * b;
        double ss = L - 0.0894841775 * a - 1.2914855480 * b;
        double l = ll * ll * ll, m = mm * mm * mm, s = ss * ss * ss;
        double r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
        double g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
        double bl = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s;
        return new int[] {
                clamp255((int) Math.round(linearToSrgb(r) * 255)),
                clamp255((int) Math.round(linearToSrgb(g) * 255)),
                clamp255((int) Math.round(linearToSrgb(bl) * 255))
        };
    }

    private static String safeMessage(Throwable t) {
        String s = t.getMessage();
        if (s == null) return "";
        s = s.replace('\n', ' ').replace('\r', ' ');
        return s.length() > 160 ? s.substring(0, 160) : s;
    }
}
