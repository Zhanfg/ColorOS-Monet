package dev.axymorrsen.artplusauto

import android.content.res.Configuration

internal object UxConfigPoke {
    @JvmStatic
    fun main(args: Array<String>) {
        require(args.size == 1) { "expected one ux icon config value" }
        val configValue = java.lang.Long.decode(args[0])

        val amType = Class.forName("android.app.ActivityManager")
        val am = amType.getMethod("getService").invoke(null)
        val iamType = Class.forName("android.app.IActivityManager")

        val readConfiguration = iamType.getMethod("getConfiguration")
        val writeConfiguration = iamType.getMethod("updateConfiguration", Configuration::class.java)
        val config = readConfiguration.invoke(am) as Configuration

        val extraGetter = config.javaClass.getMethod("getOplusExtraConfiguration")
        val oplusExtra = extraGetter.invoke(config)

        val uxField = oplusExtra.javaClass.getField("mUxIconConfig")
        uxField.setLong(oplusExtra, configValue)

        val themeChanged = oplusExtra.javaClass.getField("mThemeChanged")
        themeChanged.setInt(oplusExtra, themeChanged.getInt(oplusExtra) + 1)

        writeConfiguration.invoke(am, config)
        println("ux-icon-config=" + java.lang.Long.toUnsignedString(configValue))
    }
}
