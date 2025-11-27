# Android Component Test Generator Usage

This helper script scans `app/src/main/java` for Activities, Services, BroadcastReceivers, and ViewModels, then creates Mockito-based local unit tests under `app/src/test/java`. It can also append JaCoCo reporting to `app/build.gradle` and summarize coverage from a JaCoCo XML report.

## Prerequisites
- Python 3.8+
- An Android project layout that includes `app/src/main/java` and `app/build.gradle`
- Gradle wrapper (`./gradlew`) available for running tests and generating coverage reports

## Basic test generation
From the project root:

```bash
python tools/android_component_test_generator.py
```

This will:
1. Scan `app/src/main/java` for supported Android components.
2. Generate Java unit tests beneath `app/src/test/java`, mirroring the package structure.
3. Skip any existing test files unless you pass `--force` to overwrite them.

Example (overwriting any existing generated tests):

```bash
python tools/android_component_test_generator.py --force
```

## Generating a test for a single file
Use `--source-file` to point at a specific Activity, Service, BroadcastReceiver, or ViewModel source. The test will be written
under `app/src/test/java` following the same package path (for example, `com.example.ui.MainActivity` becomes `app/src/test/java
/com/example/ui/MainActivityTest.java`).

```bash
python tools/android_component_test_generator.py --source-file app/src/main/java/com/example/ui/MainActivity.java
```

## Scanning a different module
Use `--source-root` to scan a different module or nonstandard source directory (the path can be absolute or relative to the project root):

```bash
python tools/android_component_test_generator.py --source-root library-module/src/main/java
```

This only affects the discovery path; generated tests are still written under `app/src/test/java` (matching the source package), so ensure that module is on your test classpath.

## Dependency handling philosophy
- The generator does **not** resolve or wire dependencies across modules. It simply validates that each component class can be resolved by name and that Mockito can create a lenient double for it.
- Collaborators such as `Context`, `Intent`, `SavedStateHandle`, and the component under test are provided as Mockito mocks, so the tests avoid real Android framework initialization.
- If your component depends on types from other modules, they must be available on the test classpath; otherwise, adjust the generated test manually or supply additional test fixtures/mocks.

## Enabling JaCoCo HTML coverage reports
To append a minimal JaCoCo configuration to `app/build.gradle` during generation, add `--jacoco`:

```bash
python tools/android_component_test_generator.py --jacoco
```

> The snippet adds the JaCoCo plugin, configures XML/HTML reports, and wires `jacocoTestReport` to run after unit tests.

## Generating and summarizing coverage
1. Run unit tests and build the JaCoCo report (after enabling the snippet above):

   ```bash
   ./gradlew test jacocoTestReport
   ```

2. Summarize coverage from the JaCoCo XML output:

   ```bash
   python tools/android_component_test_generator.py \
     --coverage-report app/build/reports/jacoco/test/jacocoTestReport.xml
   ```

The summary prints covered and missed instructions plus the overall percentage. You can combine `--jacoco` and `--coverage-report` in a single invocation if you want to append the Gradle snippet and summarize an existing report at once.

## Targeting a different project root
If you run the script outside the Android project directory, point `--project-root` at the project root:

```bash
python tools/android_component_test_generator.py \
  --project-root /path/to/android/project \
  --jacoco \
  --coverage-report /path/to/android/project/app/build/reports/jacoco/test/jacocoTestReport.xml
```
