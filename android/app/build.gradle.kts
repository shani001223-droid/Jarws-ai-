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
        versionCode = 13
        versionName = "0.8.5"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

// Free bundled offline Latin OCR for Roman Urdu/English; no cloud API key.
dependencies {
    implementation("com.google.mlkit:text-recognition:16.0.1")
}
