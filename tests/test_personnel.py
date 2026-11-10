import importlib.util
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("personnel", ROOT / ".devcontainer/personnel/setup.py")
personnel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(personnel)


class PersonnelTest(unittest.TestCase):
    def test_missing_extensions_and_teacher_vsix_are_installed(self):
        config = json.loads((ROOT / ".devcontainer/personnel/devcontainer.json").read_text())
        extensions = config["customizations"]["vscode"]["extensions"]
        installed = ["myriad-dreamin.tinymist", "OCamlLabs.ocaml-platform"]
        with patch.object(personnel.subprocess, "check_output", return_value="\n".join(installed)), patch.object(personnel.subprocess, "run") as run:
            personnel.install_extensions()
        marketplace = [call.args[0][-1] for call in run.call_args_list[:-1]]
        self.assertEqual(marketplace, [extension for extension in extensions if extension.lower() not in {value.lower() for value in installed}])
        self.assertNotIn("qfortier.vscode-mpi-exercices", marketplace)
        teacher = run.call_args_list[-1]
        self.assertEqual(teacher.args[0], ["sh", str(ROOT / ".devcontainer/install-extension.sh")])
        self.assertTrue(teacher.kwargs["env"]["MPI_TP_EXTENSION_URL"].endswith("/vscode-mpi-exercices.vsix"))
        self.assertTrue(teacher.kwargs["env"]["MPI_TP_EXTENSION_CACHE"].endswith("/mpi-exercices-extension"))

    def test_workspace_is_opened_once_after_reconnections(self):
        with TemporaryDirectory() as directory, patch.object(personnel.subprocess, "run") as run:
            marker = Path(directory) / "opened"
            personnel.open_workspace(marker)
            personnel.open_workspace(marker)
            run.assert_called_once()

    def test_workspace_open_failure_can_be_retried(self):
        with TemporaryDirectory() as directory, patch.object(personnel.subprocess, "run") as run:
            marker = Path(directory) / "opened"
            run.side_effect = OSError("VS Code indisponible")
            with self.assertRaises(OSError):
                personnel.open_workspace(marker)
            self.assertFalse(marker.exists())
            run.side_effect = None
            personnel.open_workspace(marker)
            self.assertTrue(marker.exists())

    def git(self, *args):
        return subprocess.check_output(["git", *map(str, args)], text=True, stderr=subprocess.DEVNULL).strip()

    def source(self, root, name):
        source = root / name
        self.git("init", "-b", "main", source)
        (source / "README.md").write_text("Exemple\n")
        self.git("-C", source, "add", "README.md")
        self.git("-C", source, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "Initial")
        return str(source)

    def test_rerun_preserves_branch_and_work(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            origins = {"exercices": self.source(root, "source")}
            parent = root / "workspace"
            personnel.clone_repositories(parent, origins)
            clone = parent / "exercices"
            self.git("-C", clone, "checkout", "-b", "travail")
            (clone / "README.md").write_text("Travail en cours\n")
            personnel.clone_repositories(parent, origins)
            self.assertEqual(self.git("-C", clone, "branch", "--show-current"), "travail")
            self.assertEqual((clone / "README.md").read_text(), "Travail en cours\n")

    def test_existing_directory_is_preserved(self):
        with TemporaryDirectory() as directory:
            parent = Path(directory)
            target = parent / "exercices"
            target.mkdir()
            (target / "travail.txt").write_text("À conserver")
            with self.assertRaises(RuntimeError):
                personnel.clone_repositories(parent, {"exercices": "inutilisé"})
            self.assertEqual((target / "travail.txt").read_text(), "À conserver")

    def test_existing_foreign_repository_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            origins = {"exercices": self.source(root, "source")}
            parent = root / "workspace"
            personnel.clone_repositories(parent, origins)
            self.git("-C", parent / "exercices", "remote", "set-url", "origin", "autre-origine")
            with self.assertRaises(RuntimeError):
                personnel.clone_repositories(parent, origins)

    def test_workspace_and_permissions_cover_cloned_repositories(self):
        config = json.loads((ROOT / ".devcontainer/personnel/devcontainer.json").read_text())
        workspace = json.loads((ROOT / "personnel.code-workspace").read_text())
        repositories = set(personnel.REPOSITORIES)
        self.assertEqual({folder["name"] for folder in workspace["folders"]}, repositories | {"tp-environnement"})
        permissions = config["customizations"]["codespaces"]["repositories"]
        self.assertEqual(set(permissions), {f"mpi-informatique/{name}" for name in repositories})
        self.assertTrue(all(value["permissions"]["contents"] == "write" for value in permissions.values()))
        student = json.loads((ROOT / ".devcontainer/devcontainer.json").read_text())
        self.assertNotIn("codespaces", student["customizations"])


if __name__ == "__main__":
    unittest.main()
