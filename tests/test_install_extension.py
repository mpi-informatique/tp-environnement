"""Vérifier le téléchargement réel par curl, sans réseau externe ni installation VS Code."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest


INSTALLER = Path(__file__).resolve().parents[1] / '.devcontainer/install-extension.sh'


@unittest.skipUnless(shutil.which('curl'), 'curl est nécessaire')
class InstallExtensionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix='mpi release test ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cache = self.root / 'cache'
        self.log = self.root / 'installations.jsonl'
        self.content = b'VSIX version 1'
        self.etag = '"version-1"'
        self.mode = 'ok'
        self.requests = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                if self.path == '/latest/download/vscode-mpi-tp.vsix':
                    self.send_response(302)
                    self.send_header('Location', '/release/vscode-mpi-tp.vsix')
                    self.end_headers()
                    return
                owner.requests.append(self.headers.get('If-None-Match'))
                if owner.mode == 'offline':
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                if owner.mode == 'missing':
                    self.send_error(404)
                    return
                if self.headers.get('If-None-Match') == owner.etag and owner.mode == 'ok':
                    self.send_response(304)
                    self.send_header('ETag', owner.etag)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header('ETag', owner.etag)
                self.send_header('Content-Length', str(len(owner.content) + (10 if owner.mode == 'interrupted' else 0)))
                self.end_headers()
                self.wfile.write(owner.content)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        binary = self.root / 'bin'
        binary.mkdir()
        code = binary / 'code'
        code.write_text(f'#!{sys.executable}\n' + '''
import json, os, sys
from pathlib import Path
assert sys.argv[1] == '--install-extension' and sys.argv[3] == '--force'
content = Path(sys.argv[2]).read_bytes().decode()
with open(os.environ['MPI_TEST_INSTALL_LOG'], 'a') as log:
    log.write(json.dumps(content) + '\\n')
sys.exit(1 if content.startswith('INVALID') else 0)
''')
        code.chmod(0o755)
        # Aucune construction ne doit être nécessaire dans le conteneur.
        for name in ['node', 'npm', 'git']:
            forbidden = binary / name
            forbidden.write_text('#!/bin/sh\necho "Outil de construction appelé" >&2\nexit 99\n')
            forbidden.chmod(0o755)
        self.env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'], MPI_TP_EXTENSION_CACHE=str(self.cache), MPI_TP_EXTENSION_URL=f'http://127.0.0.1:{self.server.server_port}/latest/download/vscode-mpi-tp.vsix', MPI_TEST_INSTALL_LOG=str(self.log))

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def install(self, success=True):
        result = subprocess.run(['sh', str(INSTALLER)], env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        self.assertEqual(list(self.cache.glob('download.*')), [], 'Nettoyer les téléchargements temporaires')
        return result

    def installed(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_download_unchanged_and_updated_release(self):
        self.install()
        self.assertEqual((self.cache / 'vscode-mpi-tp.vsix').read_bytes(), self.content)
        self.install()
        self.assertEqual(self.requests, [None, '"version-1"'])
        self.content = b'VSIX version 2'
        self.etag = '"version-2"'
        self.install()
        self.assertEqual(self.installed(), ['VSIX version 1', 'VSIX version 1', 'VSIX version 2'])
        self.assertEqual((self.cache / 'release.etag').read_text().strip(), self.etag)

    def test_offline_and_interrupted_download_keep_cache(self):
        self.install()
        for mode in ['offline', 'missing', 'interrupted']:
            with self.subTest(mode=mode):
                self.mode = mode
                self.content = b'VSIX version incomplete'
                self.etag = '"incomplete"'
                result = self.install()
                self.assertIn('version en cache', result.stderr)
                self.assertEqual((self.cache / 'vscode-mpi-tp.vsix').read_bytes(), b'VSIX version 1')
                self.assertEqual((self.cache / 'release.etag').read_text().strip(), '"version-1"')

    def test_invalid_vsix_does_not_replace_working_cache(self):
        self.install()
        self.content = b'INVALID VSIX'
        self.etag = '"invalid"'
        self.install()
        self.assertEqual(self.installed(), ['VSIX version 1', 'INVALID VSIX', 'VSIX version 1'])
        self.assertEqual((self.cache / 'vscode-mpi-tp.vsix').read_bytes(), b'VSIX version 1')
        self.assertEqual((self.cache / 'release.etag').read_text().strip(), '"version-1"')

    def test_missing_release_without_cache_fails(self):
        self.mode = 'missing'
        result = self.install(success=False)
        self.assertIn('aucune version en cache', result.stderr)
        self.assertFalse(self.log.exists())

    def test_invalid_first_download_can_be_retried(self):
        self.content = b'INVALID first VSIX'
        self.install(success=False)
        self.assertFalse((self.cache / 'vscode-mpi-tp.vsix').exists())
        self.assertFalse((self.cache / 'release.etag').exists())
        self.content = b'VSIX valid retry'
        self.install()
        self.assertEqual(self.requests, [None, None])
        self.assertEqual((self.cache / 'vscode-mpi-tp.vsix').read_bytes(), self.content)

    def test_missing_vsix_ignores_stale_etag(self):
        self.install()
        (self.cache / 'vscode-mpi-tp.vsix').unlink()
        self.install()
        self.assertEqual(self.requests, [None, None])


if __name__ == '__main__':
    unittest.main()
