plugins {
    id("com.android.application")
}

android {
    namespace = "dev.zhanfg.colorosmonet.overlay.settings"
    compileSdk = 35

    defaultConfig {
        applicationId = "dev.zhanfg.colorosmonet.overlay.settings"
        minSdk = 31
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
    }

    val releaseKeystore = System.getenv("MONET_KEYSTORE_FILE")
    if (!releaseKeystore.isNullOrBlank()) {
        signingConfigs {
            create("release") {
                storeFile = file(releaseKeystore)
                storePassword = System.getenv("MONET_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("MONET_KEY_ALIAS")
                keyPassword = System.getenv("MONET_KEY_PASSWORD")
            }
        }
        buildTypes.getByName("release").signingConfig = signingConfigs.getByName("release")
    }

    buildFeatures { buildConfig = false }
    packaging { resources.excludes += setOf("META-INF/**") }
}
