const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/login.js'), 'utf8');

async function login(responseOk, role = 'STUDENT') {
  const controls = { '#login': { value: ' aluno.demo ' }, '#password': { value: 'example-password' },
    '#login-error': { textContent: '' } };
  const button = { disabled: false };
  let submit, request, redirected, reloaded = false;
  const form = {
    addEventListener(_name, callback) { submit = callback; },
    querySelector() { return button; },
  };
  const context = vm.createContext({
    document: { querySelector(selector) { return selector === '#login-form' ? form : controls[selector]; } },
    fetch: async (url, options) => { request = { url, options }; return { ok: responseOk, json: async () => ({ role }) }; },
    location: { replace(url) { redirected = url; }, reload() { reloaded = true; } },
  });
  vm.runInContext(source, context);
  await submit({ preventDefault() {} });
  return { controls, request, redirected, reloaded, button };
}

test('login sends only credentials and clears the password on success', async () => {
  const ui = await login(true);
  assert.equal(ui.request.url, '/auth/login');
  assert.deepEqual(JSON.parse(ui.request.options.body), { login: 'aluno.demo', password: 'example-password' });
  assert.equal(ui.request.options.credentials, 'same-origin');
  assert.equal(ui.controls['#password'].value, '');
  assert.equal(ui.redirected, '/#student/home');
  assert.equal(ui.reloaded, true);
  assert.equal(ui.button.disabled, false);
});

for (const [role, destination] of [
  ['STUDENT', '/#student/home'],
  ['TEACHER', '/#teacher/home'],
  ['SCHOOL_MANAGER', '/#management/home'],
  ['NETWORK_MANAGER', '/#management/home'],
]) test(`successful login opens the module authorized by the server: ${role}`, async () => {
  // The typed login remains aluno.demo: only the server's role determines the route.
  const ui = await login(true, role);
  assert.equal(ui.redirected, destination);
  assert.equal(ui.reloaded, true);
  assert.equal(ui.controls['#password'].value, '');
});

test('an unsupported role falls back to the entry page without granting a module', async () => {
  const ui = await login(true, 'UNSUPPORTED');
  assert.equal(ui.redirected, '/');
});

test('login failure reveals no role selector or credential detail', async () => {
  const ui = await login(false);
  assert.equal(ui.controls['#login-error'].textContent, 'Credenciais inválidas.');
  assert.equal(ui.controls['#password'].value, '');
  assert.equal(ui.redirected, undefined);
  assert.equal(ui.reloaded, false);
});
