pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "ColorOS-Monet"
include(":overlays:x")
include(":overlays:tim")
include(":overlays:coolapk")
include(":overlays:coloros-settings")
