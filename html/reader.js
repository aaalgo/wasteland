'use strict';

const poem = document.getElementById('poem');
const panel = document.getElementById('fragment-panel');
const content = document.getElementById('fragment-content');
const status = document.getElementById('status');
const initialContent = content.innerHTML;
let selected = null;
let currentTopic = null;

// Give each topic its own pastel shade, shared by all its occurrences.
const references = [...poem.querySelectorAll('.reference')];
const topics = [...new Set(references.map(ref => ref.dataset.topic))].sort();
const topicHues = new Map(topics.map((topic, index) => [topic, (index * 137.508) % 360]));
for (const ref of references) {
  ref.style.setProperty('--fragment-hue', topicHues.get(ref.dataset.topic));
}

function destination(topic, id) {
  const params = new URLSearchParams({ topic });
  if (id) params.set('ref', id);
  return '#' + params.toString();
}

function navigate(topic, id) {
  const hash = destination(topic, id);
  if (location.hash === hash) render();
  else location.hash = hash;
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function render() {
  const params = new URLSearchParams(location.hash.slice(1));
  const topic = params.get('topic');
  if (selected) selected.classList.remove('selected');
  selected = null;
  if (!topic) {
    content.innerHTML = initialContent;
    currentTopic = null;
    status.textContent = 'Select a passage to open a fragment.';
    return;
  }
  const data = window.WASTELAND_DATA;
  if (!data || data.schema_version !== 1) {
    content.replaceChildren(element('h2', 'Fragments could not be loaded'),
      element('p', 'Reload the page to retry. If the problem persists, run python update.py again.'));
    const retry = element('button', 'Reload');
    retry.addEventListener('click', () => location.reload());
    content.append(retry);
    status.textContent = 'Fragments could not be loaded.';
    return;
  }
  if (!Object.hasOwn(data.fragments, topic)) {
    content.replaceChildren(element('h2', 'Unknown fragment'), element('p', topic));
    currentTopic = null;
    status.textContent = 'Unknown fragment.';
    return;
  }
  const fragment = data.fragments[topic];
  const ref = fragment.references.find(item => item.id === params.get('ref'));
  if (topic !== currentTopic) {
    const heading = element('h2', fragment.title);
    const body = element('div', undefined, 'fragment-body');
    // HTML comes only from the builder's Markdown renderer (raw HTML disabled).
    body.innerHTML = fragment.body_html;
    content.replaceChildren(element('p', 'Fragment / ' + topic, 'eyebrow'), heading, body);
    content.append(element('h3', 'Referring passages'));
    if (!fragment.references.length) content.append(element('p', 'No referring passages.'));
    const list = element('ol', undefined, 'backlinks');
    for (const item of fragment.references) {
      const row = element('li');
      const link = element('a');
      link.href = destination(topic, item.id);
      link.dataset.ref = item.id;
      const quote = item.quote.trim().replace(/\s+/g, ' ');
      link.append(element('span', quote.length > 200 ? quote.slice(0, 197) + '…' : quote));
      link.append(element('small', item.start_line === item.end_line
        ? 'Source line ' + item.start_line
        : `Source lines ${item.start_line}–${item.end_line}`));
      link.addEventListener('click', event => {
        event.preventDefault();
        navigate(topic, item.id);
      });
      row.append(link);
      list.append(row);
    }
    content.append(list);
    currentTopic = topic;
    panel.scrollTop = 0;
  }
  for (const link of content.querySelectorAll('[data-ref]')) {
    if (ref && link.dataset.ref === ref.id) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
  if (ref) {
    selected = document.getElementById(ref.id);
    if (selected && selected.dataset.topic === topic) {
      selected.classList.add('selected');
      selected.scrollIntoView({ block: 'center', inline: 'nearest' });
      selected.focus({ preventScroll: true });
    }
  }
  status.textContent = 'Opened ' + fragment.title;
}

poem.addEventListener('click', event => {
  const ref = event.target.closest('.reference');
  if (ref) navigate(ref.dataset.topic, ref.id);
});
poem.addEventListener('keydown', event => {
  if (event.key !== 'Enter') return;
  const ref = event.target.closest('.reference');
  if (ref) {
    event.preventDefault();
    navigate(ref.dataset.topic, ref.id);
  }
});
window.addEventListener('hashchange', render);
render();
