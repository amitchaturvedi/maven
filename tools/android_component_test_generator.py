"""Utility to scaffold Android unit tests and coverage reporting.

This script scans ``app/src/main/java`` for Android components (Activities,
Services, BroadcastReceivers, and ViewModels), generates Mockito-based local
unit tests, ensures JaCoCo HTML reporting is configured in Gradle, and can
summarize coverage from JaCoCo XML reports.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
import xml.etree.ElementTree as ET


COMPONENT_PATTERNS = {
    "Activity": re.compile(r"\bclass\s+(\w+).*?(extends|:)\s+[\w\.]*?(\w*Activity)\b", re.S),
    "Service": re.compile(r"\bclass\s+(\w+).*?(extends|:)\s+[\w\.]*?(\w*Service)\b", re.S),
    "BroadcastReceiver": re.compile(r"\bclass\s+(\w+).*?(extends|:)\s+[\w\.]*?BroadcastReceiver\b", re.S),
    "ViewModel": re.compile(r"\bclass\s+(\w+).*?(extends|:)\s+[\w\.]*?ViewModel\b", re.S),
}

SUPPORTED_EXTENSIONS = {".java", ".kt"}


@dataclass
class Component:
    name: str
    package: str
    file_path: Path
    type: str

    @property
    def qualified_name(self) -> str:
        return f"{self.package}.{self.name}" if self.package else self.name

    @property
    def test_class_name(self) -> str:
        return f"{self.name}Test"

    @property
    def test_path(self) -> Path:
        package_dir = Path(*self.package.split(".")) if self.package else Path()
        return Path("app/src/test/java") / package_dir / f"{self.test_class_name}.java"


def parse_component_file(path: Path) -> List[Component]:
    """Parse a single source file and return any supported components it contains."""

    components: List[Component] = []

    if path.suffix not in SUPPORTED_EXTENSIONS or not path.is_file():
        print(f"Skipping unsupported or missing file: {path}")
        return components

    text = path.read_text(encoding="utf-8", errors="ignore")
    package_match = re.search(r"^\s*package\s+([\w\.]+)", text, re.M)
    package = package_match.group(1) if package_match else ""

    for component_type, pattern in COMPONENT_PATTERNS.items():
        match = pattern.search(text)
        if not match:
            continue
        class_name = match.group(1)
        components.append(
            Component(
                name=class_name,
                package=package,
                file_path=path,
                type=component_type,
            )
        )
    return components


def discover_components(root: Path, source_root: Path) -> List[Component]:
    if not source_root.is_absolute():
        source_root = root / source_root
    components: List[Component] = []

    if not source_root.exists():
        print(f"No source directory found at {source_root}. Nothing to scan.")
        return components

    for path in source_root.rglob("*"):
        components.extend(parse_component_file(path))
    return components


def ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def generate_imports(component: Component) -> List[str]:
    imports = [
        "org.junit.Test",
        "org.junit.runner.RunWith",
        "org.junit.Assert",
        "org.mockito.Mock",
        "org.mockito.Mockito",
        "org.mockito.junit.MockitoJUnitRunner",
    ]

    if component.type in {"Activity", "Service", "BroadcastReceiver"}:
        imports.extend([
            "android.content.Context",
            "android.content.Intent",
            "android.util.Log",
        ])
    if component.type == "BroadcastReceiver":
        imports.append("android.content.BroadcastReceiver")
    if component.type == "Activity":
        imports.append("android.app.Activity")
    if component.type == "Service":
        imports.append("android.app.Service")
    if component.type == "ViewModel":
        imports.extend([
            "androidx.lifecycle.ViewModel",
            "androidx.lifecycle.SavedStateHandle",
        ])
    imports.append(component.qualified_name)
    return sorted(set(imports))


def generate_valid_invalid_tests(component: Component) -> str:
    valid_test = f"""
    @Test
    public void resolvesClassByName() throws Exception {{
        Class<?> clazz = Class.forName("{component.qualified_name}");
        Assert.assertNotNull(clazz);
    }}
    """

    invalid_test = f"""
    @Test(expected = ClassNotFoundException.class)
    public void invalidClassNameThrows() throws Exception {{
        Class.forName("{component.qualified_name}_Missing");
    }}
    """
    return valid_test + "\n" + invalid_test


def generate_mockito_test(component: Component) -> str:
    target_name = component.name
    base_mock = f"{target_name} instance = Mockito.mock({target_name}.class, Mockito.withSettings().lenient());"

    context_setup = ""
    if component.type in {"Activity", "Service", "BroadcastReceiver"}:
        context_setup = "Mockito.when(context.getApplicationContext()).thenReturn(context);"

    collaborator = "SavedStateHandle handle = new SavedStateHandle();" if component.type == "ViewModel" else "Intent intent = Mockito.mock(Intent.class);"

    return f"""
    @Test
    public void canCreateLenientMockitoDouble() {{
        {base_mock}
        {context_setup}
        {collaborator}
        Assert.assertNotNull(instance);
    }}
    """


def test_body(component: Component) -> str:
    tests = [generate_valid_invalid_tests(component), generate_mockito_test(component)]
    return "\n".join(tests)


def test_class(component: Component) -> str:
    imports = "\n".join(f"import {item};" for item in generate_imports(component))
    body = test_body(component)
    package_line = f"package {component.package};" if component.package else ""

    mocks = """
    @Mock Context context;
    """
    if component.type == "BroadcastReceiver":
        mocks += "    @Mock Intent intent;\n"
    elif component.type == "Activity":
        mocks += "    @Mock Intent intent;\n"
    elif component.type == "Service":
        mocks += "    @Mock Intent intent;\n"
    elif component.type == "ViewModel":
        mocks = "    @Mock SavedStateHandle savedStateHandle;\n"

    return f"""
{package_line}

{imports}

@RunWith(MockitoJUnitRunner.class)
public class {component.test_class_name} {{
{mocks}
{body}
}}
"""


def write_tests(components: Iterable[Component], force: bool = False) -> List[Path]:
    written: List[Path] = []
    for component in components:
        destination = component.test_path
        ensure_directory(destination)
        content = test_class(component)
        if destination.exists() and not force:
            print(f"Skipping {destination} (already exists). Use --force to overwrite.")
            continue
        destination.write_text(content, encoding="utf-8")
        written.append(destination)
        print(f"Created {destination.relative_to(Path.cwd())}")
    return written


JACOCO_SNIPPET = """
// Added by android_component_test_generator.py
plugins { id 'jacoco' }

jacoco {
    toolVersion = "0.8.10"
}

tasks.withType(Test) {
    finalizedBy jacocoTestReport
}

jacocoTestReport {
    dependsOn test
    reports {
        xml.required = true
        csv.required = false
        html.required = true
    }
}
"""


def ensure_jacoco(build_gradle: Path) -> None:
    if not build_gradle.exists():
        print(f"Gradle file {build_gradle} not found; skipping JaCoCo integration.")
        return

    content = build_gradle.read_text(encoding="utf-8")
    if "jacocoTestReport" in content and "jacoco" in content:
        print("JaCoCo configuration already detected.")
        return

    updated = content.rstrip() + "\n\n" + JACOCO_SNIPPET
    build_gradle.write_text(updated, encoding="utf-8")
    print(f"Appended JaCoCo configuration to {build_gradle}")


@dataclass
class CoverageSummary:
    covered: float
    missed: float

    @property
    def total(self) -> float:
        return self.covered + self.missed

    @property
    def coverage_pct(self) -> float:
        return 0.0 if self.total == 0 else (self.covered / self.total) * 100


def parse_coverage(report: Path) -> Optional[CoverageSummary]:
    if not report.exists():
        print(f"Coverage report {report} not found.")
        return None

    tree = ET.parse(report)
    root = tree.getroot()
    counter = root.find("counter[@type='INSTRUCTION']")
    if counter is None:
        print("No instruction counter found in report.")
        return None
    covered = float(counter.attrib.get("covered", 0))
    missed = float(counter.attrib.get("missed", 0))
    return CoverageSummary(covered=covered, missed=missed)


def summarize_coverage(report: Path) -> None:
    summary = parse_coverage(report)
    if not summary:
        return

    print("Coverage summary (JaCoCo):")
    print(f"  Covered instructions: {summary.covered}")
    print(f"  Missed instructions:  {summary.missed}")
    print(f"  Coverage:            {summary.coverage_pct:.2f}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Android tests and coverage helpers")
    parser.add_argument("--project-root", default=Path.cwd(), type=Path, help="Root of the Android project")
    parser.add_argument(
        "--source-root",
        default=Path("app/src/main/java"),
        type=Path,
        help="Relative or absolute source directory to scan (e.g., module/src/main/java)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing test files")
    parser.add_argument("--jacoco", action="store_true", help="Ensure JaCoCo HTML reporting is configured in app/build.gradle")
    parser.add_argument("--coverage-report", type=Path, help="Path to a JaCoCo XML report to summarize")
    parser.add_argument(
        "--source-file",
        type=Path,
        help=(
            "Path to a single Activity/Service/BroadcastReceiver/ViewModel source file "
            "for targeted test generation"
        ),
    )

    args = parser.parse_args()
    root = args.project_root

    if args.source_file:
        target_file = args.source_file if args.source_file.is_absolute() else root / args.source_file
        components = parse_component_file(target_file)
        if components:
            print(f"Discovered {len(components)} component(s) in {target_file}")
            write_tests(components, force=args.force)
        else:
            print(f"No supported components found in {target_file}.")
    else:
        components = discover_components(root, args.source_root)
        if components:
            print(f"Discovered {len(components)} Android components")
            write_tests(components, force=args.force)
        else:
            print("No Android components detected.")

    if args.jacoco:
        ensure_jacoco(root / "app" / "build.gradle")

    if args.coverage_report:
        summarize_coverage(args.coverage_report)


if __name__ == "__main__":
    main()
