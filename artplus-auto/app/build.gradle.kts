plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "dev.axymorrsen.artplusauto"
    compileSdk = 35

    defaultConfig {
        applicationId = "dev.axymorrsen.artplusauto"
        minSdk = 33
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0-alpha1"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
}
