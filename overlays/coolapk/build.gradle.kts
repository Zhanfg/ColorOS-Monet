plugins {
    id("com.android.application")
}

val generatedRes = layout.buildDirectory.dir("generated/monet-res")

val generateMonetResources by tasks.registering(Exec::class) {
    inputs.dir(layout.projectDirectory.dir("mapping"))
    inputs.file(rootProject.layout.projectDirectory.file("tools/generate_colors.py"))
    outputs.dir(generatedRes)
    commandLine(
        "python3",
        rootProject.layout.projectDirectory.file("tools/generate_colors.py").asFile.absolutePath,
        "--mapping", layout.projectDirectory.dir("mapping").asFile.absolutePath,
        "--output", generatedRes.get().asFile.absolutePath
    )
}

android {
    namespace = "dev.zhanfg.colorosmonet.overlay.coolapk"
    compileSdk = 35

    defaultConfig {
        applicationId = "dev.zhanfg.colorosmonet.overlay.coolapk"
        minSdk = 31
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
    }

    sourceSets.getByName("main").res.srcDir(generatedRes)
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

    buildFeatures {
        buildConfig = false
    }
    packaging {
        resources.excludes += setOf("META-INF/**")
    }
}

tasks.named("preBuild").configure { dependsOn(generateMonetResources) }
