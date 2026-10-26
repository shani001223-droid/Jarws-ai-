plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.valtron.jarvis"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.valtron.jarvis"
        minSdk = 26
        targetSdk = 32
        versionCode = 12
        versionName = "0.8.4"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}
