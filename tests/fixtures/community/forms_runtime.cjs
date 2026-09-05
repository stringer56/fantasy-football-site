// Test-only Apps Script service doubles. No Google connections or submissions.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const forms = new Map(), properties = new Map(), logs = [];
function item(type) {
  return {type, setTitle(v) { this.title = v; return this; },
    setRequired(v) { this.required = v; return this; },
    setChoiceValues(v) { this.choices = v; return this; },
    setHelpText(v) { this.help = v; return this; }};
}
function makeForm(title, published) {
  assert.equal(published, false);
  const f = {title, published, accepting: true, items: [], id: 'test-form-' + (forms.size + 1),
    getId() { return this.id; },
    setAcceptingResponses(v) { this.accepting = v; return this; },
    isAcceptingResponses() { return this.accepting; },
    setCollectEmail(v) { this.email = v; return this; },
    setLimitOneResponsePerUser(v) { this.login = v; return this; },
    setPublishingSummary(v) { this.summary = v; return this; },
    setAllowResponseEdits(v) { this.edits = v; return this; },
    setDescription(v) { assert.equal(this.accepting, false); this.description = v; return this; },
    addMultipleChoiceItem() { const i = item('choice'); this.items.push(i); return i; },
    addListItem() { const i = item('dropdown'); this.items.push(i); return i; },
    getPublishedUrl() { return 'https://docs.google.com/forms/d/e/' + this.id + '/viewform'; }
  };
  forms.set(f.id, f);
  return f;
}
const context = vm.createContext({
  console: {log: v => logs.push(v)},
  PropertiesService: {getScriptProperties: () => ({getProperty: k => properties.get(k),
    setProperty: (k, v) => properties.set(k, v)})},
  FormApp: {create: makeForm, openById: id => { assert.ok(forms.has(id)); return forms.get(id); }}
  // Any use of Drive, networking, email or response submission during creation fails.
});
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8'), context);
vm.runInContext('createCommunityForms()', context);
const config = JSON.parse(vm.runInContext('JSON.stringify(RTG)', context));
assert.equal(forms.size, 3);
[...forms.values()].forEach((f, index) => {
  const spec = config.forms[index];
  assert.equal(f.title, spec.title);
  for (const flag of ['published', 'accepting', 'email', 'login', 'summary', 'edits']) assert.equal(f[flag], false);
  assert.equal(f.items.length, spec.questions.length);
  f.items.forEach((i, n) => {
    assert.equal(i.required, true);
    assert.equal(i.title, spec.questions[n].title);
    assert.equal(i.type, spec.questions[n].type);
    assert.deepEqual(Array.from(i.choices || []), spec.questions[n].choices);
  });
});
assert.equal(logs.filter(v => v.includes('PUBLIC RESPONDER URL:')).length, 3);
assert.ok(logs.every(v => !/https?:\/\/\S*(?:\/edit|spreadsheets)/.test(v)));
// Reusing a commissioner-opened Form must neither close it nor claim it is closed.
[...forms.values()][0].accepting = true;
logs.length = 0;
vm.runInContext('createCommunityForms()', context);
assert.equal(forms.size, 3);
assert.equal([...forms.values()][0].accepting, true);
assert.equal(logs.filter(v => v.includes('Accepting responses: YES')).length, 1);
console.log('Three Forms: fields, privacy defaults, responder-only URLs and safe reuse passed (mock services).');
