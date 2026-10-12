const test = require('node:test');
const assert = require('node:assert/strict');
const { page } = require('./workspace-dom.cjs');
const { element, descendants } = require('./ui-dom.cjs');

const value = content => ({ value: content });
function recorded() {
  return { status: 'recorded', record: { manifest_sha256: 'a'.repeat(64), filename: 'reproducibility_manifest.json',
    manifest: {
      code_identity: { git_commit: value('c'.repeat(40)), build_id: value('pilot-01'), worktree_dirty: true },
      application_identity: { project_version: value('0.1.0'), api_version: '0.4.0', conversion_version: 'segments-v1', audit_bridge_version: value(null) },
      python_environment: { major: 3, minor: 9, micro: 6, implementation: 'CPython', dependency_manifest_filename: 'python_dependencies.txt' },
      formal_environment: { lean_version: value('4.28.0'), lake_version: value('5.0.0'), mathlib_revision: value('m'.repeat(40)) },
      problem_assets: [{ status: 'available', relative_path: 'problems/ITA2025Q1/problem.json' }], configuration_assets: [],
    } } };
}

for (const [metadata, label] of [
  [undefined, 'Metadados de reprodutibilidade não registrados nesta execução.'],
  [{ status: 'legacy_unversioned' }, 'Metadados de reprodutibilidade não registrados nesta execução.'],
  [{ status: 'unavailable' }, 'Metadados da execução indisponíveis.'],
  [recorded(), 'Metadados da execução registrados.'],
]) {
  test(`teacher report renders ${metadata?.status || 'legacy'} as a secondary disclosure`, async () => {
    const ui = await page();
    const panel = element('div');
    ui.window.ConfIAReport.render({ reproducibility: metadata, artifact_dir: '/Users/private/server',
      lean_certificate: { lean_file: '/Users/private/proof.lean', stderr: '/Users/private/compiler' },
    }, panel, { context: 'teacher' });
    const disclosure = descendants(panel).find(node => node.className?.includes('analysis-environment'));
    assert(disclosure && disclosure.tag === 'details' && !disclosure.open);
    assert.equal(disclosure.children[0].textContent, 'Ambiente da análise');
    assert(disclosure.textContent.includes(label));
    assert.doesNotMatch(panel.textContent, /\/Users\/|Execução garantidamente reproduzível/);
    if (metadata?.status === 'recorded') {
      assert.match(disclosure.textContent, /dirty \(com alterações\).*API: 0.4.0.*Python: 3.9.6.*Lean: 4.28.0.*Assets registrados: 1 de 1/s);
      assert.equal(descendants(disclosure).filter(node => node.tag === 'summary' && node.textContent === 'Detalhes técnicos').length, 1);
      assert.match(disclosure.textContent, /não é assinatura digital/);
    }
  });
}

test('metadata is rendered as text, never HTML, and unknown worktree state is explicit', async () => {
  const ui = await page();
  const panel = element('div');
  const metadata = recorded();
  metadata.record.manifest.code_identity.build_id = value('<img src=x onerror=alert(1)>');
  metadata.record.manifest.code_identity.worktree_dirty = null;
  ui.window.ConfIAReport.render({ reproducibility: metadata }, panel, { context: 'teacher' });
  assert.match(panel.textContent, /estado desconhecido/);
  assert.equal(descendants(panel).filter(node => node.tag === 'img').length, 0);
  const publicData = JSON.stringify({ artifact_dir: '/private/server', file: '/private/server/Attempt.lean',
    lean_file: '/private/server/Attempt.lean', stdout: '/private/server/diagnostic', reproducibility: metadata },
    ui.window.ConfIAReport.publicTechnicalValue);
  assert.doesNotMatch(publicData, /\/private\/server/);
  assert.equal(JSON.parse(publicData).file, null);
});

test('unexpected backend text cannot create HTML in teacher report or metadata', async () => {
  const ui = await page();
  const panel = element('div');
  const hostile = '<img src=x onerror=alert(1)><script>unsafe()</script>';
  const metadata = recorded();
  metadata.record.manifest.code_identity.build_id = value(hostile);
  ui.window.ConfIAReport.render({ feedback: hostile, reproducibility: metadata,
    pedagogical_report: { summary: hostile, result: hostile, reliability: hostile,
      attention_points: [hostile], evidence_items: [] },
  }, panel, { context: 'teacher' });
  assert.equal(descendants(panel).filter(node => ['img', 'script'].includes(node.tag)).length, 0);
  assert(descendants(panel).every(node => !Object.hasOwn(node, 'innerHTML')));
  assert(panel.textContent.includes(hostile));
  assert(panel.textContent.includes('JSON público pode conter textos ocultados'));
});
