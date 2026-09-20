import java.util.Properties
import java.io.FileInputStream

// Correct way to read local.properties in Kotlin DSL
val localProperties = Properties()
val localPropertiesFile = rootProject.file("local.properties")
if (localPropertiesFile.exists()) {
    localProperties.load(FileInputStream(localPropertiesFile))
}

// Replace "my.api.key" with whatever property you are actually trying to read
val myApiKey = localProperties.getProperty("my.api.key") ?: ""
