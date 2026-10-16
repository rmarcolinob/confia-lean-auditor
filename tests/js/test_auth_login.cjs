const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/login.js'), 'utf8');

async function login(responseOk) {
  const controls = { '#login': { value: ' aluno.demo ' }, '#password': { value: 'example-password' },
    '#login-error': { textContent: '' } };
  const button = { disabled: false };
  let submit, request, redirected;
  const form = {
    addEventListener(_name, callback) { submit = callback; },
    querySelector() { return button; },
  };
  const context = vm.createContext({
    document: { querySelector(selector) { return selector === '#login-form' ? form : controls[selector]; } },
    fetch: async (url, options) => { request = { url, options }; return { ok: responseOk }; },
    location: { replace(url) { redirected = url; } },
  });
  vm.runInContext(source, context);
  await submit({ preventDefault() {} });
  return { controls, request, redirected, button };
}

test('login sends only credentials and clears the password on success', async () => {
  const ui = await login(true);
  assert.equal(ui.request.url, '/auth/login');
  assert.deepEqual(JSON.parse(ui.request.options.body), { login: 'aluno.demo', password: 'example-password' });
  assert.equal(ui.request.options.credentials, 'same-origin');
  assert.equal(ui.controls['#password'].value, '');
  assert.equal(ui.redirected, '/');
  assert.equal(ui.button.disabled, false);
});

test('login failure reveals no role selector or credential detail', async () => {
  const ui = await login(false);
  assert.equal(ui.controls['#login-error'].textContent, 'Credenciais inválidas.');
  assert.equal(ui.controls['#password'].value, '');
  assert.equal(ui.redirected, undefined);
});
