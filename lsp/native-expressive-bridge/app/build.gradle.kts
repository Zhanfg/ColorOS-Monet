plugins {
    id("com.android.application")
}

android {
    namespace = "dev.zhanfg.colorosmonet.bridge"
    compileSdk = 37

    defaultConfig {
        applicationId = "dev.zhanfg.colorosmonet.bridge"
        minSdk = 35
        targetSdk = 37
        versionCode = 20001
        versionName = "0.2.0-alpha1"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    compileOnly("de.robv.android.xposed:api:82")
}
