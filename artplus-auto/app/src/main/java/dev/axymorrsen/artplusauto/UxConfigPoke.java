package dev.axymorrsen.artplusauto;

import android.content.res.Configuration;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * app_process entry point used by the root bridge to make ColorOS observe
 * mUxIconConfig changes immediately. It does not persist settings by itself.
 */
public final class UxConfigPoke {
    private UxConfigPoke() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("expected one ux icon config value");
        }
        long configValue = Long.decode(args[0]);

        Class<?> amType = Class.forName("android.app.ActivityManager");
        Object am = amType.getMethod("getService").invoke(null);
        Class<?> iamType = Class.forName("android.app.IActivityManager");

        Method readConfiguration = iamType.getMethod("getConfiguration");
        Method writeConfiguration = iamType.getMethod("updateConfiguration", Configuration.class);
        Configuration config = (Configuration) readConfiguration.invoke(am);

        Method extraGetter = config.getClass().getMethod("getOplusExtraConfiguration");
        Object oplusExtra = extraGetter.invoke(config);

        Field uxField = oplusExtra.getClass().getField("mUxIconConfig");
        uxField.setLong(oplusExtra, configValue);

        Field themeChanged = oplusExtra.getClass().getField("mThemeChanged");
        themeChanged.setInt(oplusExtra, themeChanged.getInt(oplusExtra) + 1);

        writeConfiguration.invoke(am, config);
        System.out.println("ux-icon-config=" + Long.toUnsignedString(configValue));
    }
}
