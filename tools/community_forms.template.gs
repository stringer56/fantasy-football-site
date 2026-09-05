// Commissioner-only. No website runtime, network forwarding, or repository credentials.
// Canonical config is inserted by scripts/build_community_forms.py.
const RTG = __RTG_CONFIG__;

function createCommunityForms() {
  const props = PropertiesService.getScriptProperties();
  RTG.forms.forEach(spec => {
    const key = 'rtg-' + RTG.season + '-' + RTG.week + '-' + spec.kind;
    let id = props.getProperty(key);
    if (!id) {
      const form = FormApp.create(spec.title, false);
      // Save immediately so reruns never silently create duplicate Forms.
      props.setProperty(key, form.getId());
      // Keep it closed even if question setup fails partway.
      form.setAcceptingResponses(false);
      form.setCollectEmail(false).setLimitOneResponsePerUser(false)
        .setPublishingSummary(false).setAllowResponseEdits(false)
        .setDescription(spec.description);
      spec.questions.forEach(q => {
        const item = q.type === 'choice' ? form.addMultipleChoiceItem() : form.addListItem();
        item.setTitle(q.title).setRequired(true);
        if (q.choices.length) item.setChoiceValues(q.choices);
        if (q.help) item.setHelpText(q.help);
      });
      id = form.getId();
    }
    const form = FormApp.openById(id);
    console.log(spec.title + ' — PUBLIC RESPONDER URL: ' + form.getPublishedUrl());
    console.log('Accepting responses: ' + (form.isAcceptingResponses() ? 'YES — existing Form; review manually' : 'NO'));
  });
  console.log('New Forms start unpublished/closed. Existing Forms are reused without changing their state. Review in Google Forms home; never share editor or Sheet links.');
}

function exportPowerCsv() { exportCommunityCsv_('power'); }
function exportPicksCsv() { exportCommunityCsv_('picks'); }
function exportVotesCsv() { exportCommunityCsv_('votes'); }

function exportCommunityCsv_(kind) {
  const spec = RTG.forms.find(f => f.kind === kind);
  const key = 'rtg-' + RTG.season + '-' + RTG.week + '-' + kind;
  const id = PropertiesService.getScriptProperties().getProperty(key);
  if (!id) throw new Error('Run createCommunityForms first.');
  const form = FormApp.openById(id);
  const headers = ['submitted_at'].concat(spec.questions.map(q => q.title));
  const rows = [headers];
  form.getResponses().forEach(response => {
    const answers = {};
    response.getItemResponses().forEach(item => { answers[item.getItem().getTitle()] = item.getResponse(); });
    const row = [response.getTimestamp().toISOString()];
    spec.questions.forEach(q => {
      const answer = String(answers[q.title] || '');
      // All supported answers are IDs or integer season/week. Fail on new/free text fields.
      if (!/^[A-Za-z0-9-]+$/.test(answer)) throw new Error('Unexpected answer; inspect privately before export.');
      row.push(answer);
    });
    rows.push(row);
  });
  if (rows.length === 1) throw new Error('No real responses to export.');
  const csv = rows.map(row => row.map(value => '"' + String(value).replace(/"/g, '""') + '"').join(',')).join('\r\n');
  // New file remains private. No permissions/sharing calls and no responses in logs.
  const name = kind + '-week-' + String(RTG.week).padStart(2, '0') + '.csv';
  DriveApp.createFile(name, csv, MimeType.CSV);
  console.log('Created private Drive file ' + name + '. Download to ignored private-vote-imports/. Do not share it.');
}
