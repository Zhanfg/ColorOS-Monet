package dev.zhanfg.colorosmonet.bridge;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public final class MainHook implements IXposedHookLoadPackage {
    private static final String TAG = "ColorOS17NativeExpressive";
    private static final String FEATURE_FLAGS =
            "com.android.settingslib.widget.theme.flags.FeatureFlagsImpl";
    private static final String EXPRESSIVE_FIELD = "isExpressiveDesignEnabled";

    // Deliberately narrow for alpha1. PermissionController and other SettingsLib
    // hosts are added only after their ColorOS 17 integration is audited.
    private static final Set<String> TARGETS;

    static {
        HashSet<String> targets = new HashSet<>();
        targets.add("com.android.settings");
        targets.add("com.android.systemui");
        TARGETS = Collections.unmodifiableSet(targets);
    }

    @Override
    public void handleLoadPackage(XC_LoadPackage.LoadPackageParam lpparam) {
        if (!TARGETS.contains(lpparam.packageName)) {
            return;
        }

        try {
            Class<?> flags = XposedHelpers.findClass(FEATURE_FLAGS, lpparam.classLoader);
            XposedHelpers.setStaticBooleanField(flags, EXPRESSIVE_FIELD, true);
            XposedBridge.log(TAG + ": native expressive flag enabled for " + lpparam.packageName);
        } catch (XposedHelpers.ClassNotFoundError ignored) {
            // Native-first fallback: if this ROM/app does not expose SettingsLib
            // expressive flags, leave the package completely untouched.
        } catch (NoSuchFieldError ignored) {
            // Same fallback for field layout changes.
        } catch (Throwable t) {
            XposedBridge.log(TAG + ": safe fallback in " + lpparam.packageName + ": " + t);
        }
    }
}
