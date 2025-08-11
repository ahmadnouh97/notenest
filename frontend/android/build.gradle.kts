allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory = rootProject.layout.buildDirectory.dir("../../build").get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

// Ensure consistent JVM targets across all modules (including plugin subprojects)
subprojects {
    // Align Kotlin and Java targets to 11 across all modules
    tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
        kotlinOptions.jvmTarget = "11"
    }
    tasks.withType<org.gradle.api.tasks.compile.JavaCompile>().configureEach {
        sourceCompatibility = "11"
        targetCompatibility = "11"
    }
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
