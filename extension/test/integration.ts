import * as vscode from 'vscode';
import assert from 'node:assert/strict';
import * as path from 'node:path';
import { readFile, writeFile } from 'node:fs/promises';
export async function run() {
  const extension = vscode.extensions.getExtension('qfortier.vscode-mpi-tp')!;
  const api = await extension.activate();
  assert.equal(api.entries.length, 1);
  assert.equal(api.course[0].id, 'tp-test');
  await api.open('tp-test');
  assert.equal(api.started.length, 1);
  const deadline = Date.now() + 20000;
  while (!api.previewStatus.get(api.started[0].directory)?.pages && Date.now() < deadline) {
    assert.equal(api.previewStatus.get(api.started[0].directory)?.error, undefined);
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.equal(api.previewStatus.get(api.started[0].directory)?.pages, 1);
  const file = path.join(api.started[0].directory, 'main.ml');
  await writeFile(file, 'let travail = 42\n');
  await api.open('tp-test');
  assert.equal(await readFile(file, 'utf8'), 'let travail = 42\n');
  assert.equal(vscode.window.tabGroups.all.length, 2);
  const groups = vscode.window.tabGroups.all;
  assert(groups[0].tabs.some(tab => tab.input instanceof vscode.TabInputText && tab.input.uri.fsPath === file));
  assert(groups[1].tabs.some(tab => tab.input instanceof vscode.TabInputWebview));
  await vscode.commands.executeCommand('mpiTp.search');
  await vscode.commands.executeCommand('workbench.action.closeQuickOpen');
}
