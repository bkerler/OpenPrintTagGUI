import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "make_flatpak.sh"


@unittest.skipUnless(os.name == "posix", "Flatpak build scripts require a POSIX host")
class MakeFlatpakTests(unittest.TestCase):
    def run_script(self, manager=None, installed=False, fail_create=False):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project with spaces"
            project.mkdir()
            shutil.copy2(SCRIPT, project)
            commands = root / "bin"
            commands.mkdir()
            log = root / "commands.log"
            for name in ("bash", "dirname", "rm"):
                (commands / name).symlink_to(shutil.which(name))

            def executable(name, content):
                path = commands / name
                path.write_text("#!/bin/bash\nset -eu\n" + content)
                path.chmod(0o755)

            executable("python3", '''
if [ "$1" = -c ]; then exit 0; fi
/bin/mkdir -p build/flatpak-venv/bin
/bin/cp "$MOCK_PYTHON" build/flatpak-venv/bin/python
''')
            executable("venv-python", '''
echo "$PWD: $*" >> "$COMMAND_LOG"
if [ "$*" = "-m briefcase create linux flatpak --no-input" ]; then
    exit "$FAIL_CREATE"
fi
''')
            executable("sudo", 'echo "$*" >> "$COMMAND_LOG"\n')
            if manager:
                executable(manager, "exit 0\n")
            if installed:
                for name in ("flatpak", "flatpak-builder"):
                    executable(name, "exit 0\n")
            result = subprocess.run(
                ["/bin/bash", str(project / "make_flatpak.sh")],
                cwd=root,
                env={**os.environ, "PATH": str(commands), "COMMAND_LOG": str(log),
                     "MOCK_PYTHON": str(commands / "venv-python"),
                     "FAIL_CREATE": "1" if fail_create else "0"},
                capture_output=True, text=True,
            )
            return result, log.read_text() if log.exists() else ""

    def test_installs_distribution_dependencies(self):
        for manager, packages in (
            ("dnf", "python3-pip"), ("apt-get", "python3-venv"),
        ):
            with self.subTest(manager=manager):
                result, log = self.run_script(manager=manager)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"{manager} install -y flatpak flatpak-builder {packages}", log)
                self.assertIn("project with spaces: -m briefcase package linux flatpak --no-input", log)

    def test_skips_installation_when_tools_are_available(self):
        result, log = self.run_script(installed=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("install -y", log)

    def test_stops_after_failed_create(self):
        result, log = self.run_script(installed=True, fail_create=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("-m briefcase build", log)
        self.assertNotIn("-m briefcase package", log)

    def test_reports_missing_package_manager(self):
        result, log = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Install flatpak", result.stderr)
        self.assertEqual(log, "")


if __name__ == "__main__":
    unittest.main()
