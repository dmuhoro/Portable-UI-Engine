import '../elements/ui-primitives.js';

function assert(condition, message = 'assertion failed') {
  if (!condition) throw new Error(message);
}

function addElement(tag, attributes = {}) {
  const element = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
  document.body.append(element);
  return element;
}

describe('Portable UI primitives', () => {
  afterEach(() => { document.body.replaceChildren(); });

  it('registers all design brief elements', () => {
    for (const tag of ['ui-button', 'ui-input', 'ui-checkbox', 'ui-select', 'ui-dialog', 'ui-tooltip', 'ui-toast', 'ui-tabs', 'ui-menu']) {
      assert(Boolean(customElements.get(tag)), `${tag} is registered`);
    }
  });

  it('emits a composed button action and honors disabled state', () => {
    const button = addElement('ui-button');
    let received = 0;
    button.addEventListener('ui-button-click', event => { received += 1; assert(event.bubbles && event.composed); });
    button.shadowRoot.querySelector('button').click();
    button.setAttribute('disabled', '');
    button.shadowRoot.querySelector('button').click();
    assert(received === 1, 'only enabled activation emits');
  });

  it('reflects input values and emits user edits', () => {
    const input = addElement('ui-input', { label: 'Email', name: 'email' });
    let detail;
    input.addEventListener('ui-input-change', event => { detail = event.detail; });
    const field = input.shadowRoot.querySelector('input');
    field.value = 'a@example.com';
    field.dispatchEvent(new Event('input', { bubbles: true }));
    assert(detail.name === 'email' && detail.value === 'a@example.com');
    assert(input.value === 'a@example.com');
  });

  it('supports checkbox state and indeterminate reflection', () => {
    const checkbox = addElement('ui-checkbox', { label: 'Select all', indeterminate: '' });
    assert(checkbox.shadowRoot.querySelector('input').indeterminate);
    checkbox.shadowRoot.querySelector('input').click();
    assert(checkbox.checked);
  });

  it('filters and selects options through the combobox contract', () => {
    const select = addElement('ui-select');
    select.options = [{ label: 'Alpha', value: 'a' }, { label: 'Beta', value: 'b' }];
    let selected;
    select.addEventListener('ui-select-change', event => { selected = event.detail.value; });
    const input = select.shadowRoot.querySelector('input');
    input.focus();
    input.value = 'Beta';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    select.shadowRoot.querySelector('[role="option"]').click();
    assert(selected === 'b' && select.value === 'b');
  });

  it('changes tabs with arrow keys and emits the selected index', () => {
    const tabs = addElement('ui-tabs');
    tabs.items = [{ label: 'Overview', content: 'Summary' }, { label: 'Logs', content: 'Events' }];
    let selected;
    tabs.addEventListener('ui-tab-change', event => { selected = event.detail.index; });
    tabs.shadowRoot.querySelector('[role="tab"]').dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    assert(selected === 1 && tabs.shadowRoot.querySelector('[role="tabpanel"]').textContent === 'Events');
  });

  it('opens native dialog and dismisses toast through public methods', () => {
    const dialog = addElement('ui-dialog', { label: 'Confirmation' });
    dialog.show();
    assert(dialog.shadowRoot.querySelector('dialog').open);
    dialog.close();
    assert(!dialog.shadowRoot.querySelector('dialog').open);

    const toast = addElement('ui-toast', { message: 'Saved', duration: '0' });
    let dismissed = false;
    toast.addEventListener('ui-toast-dismiss', () => { dismissed = true; });
    toast.dismiss();
    assert(toast.hidden && dismissed);
  });

  it('opens menu and emits the selected action', () => {
    const menu = addElement('ui-menu');
    menu.items = [{ label: 'Settings', value: 'settings', shortcut: '⌘,' }];
    let value;
    menu.addEventListener('ui-menu-select', event => { value = event.detail.value; });
    menu.shadowRoot.querySelector('button[aria-haspopup="menu"]').click();
    menu.shadowRoot.querySelector('[role="menuitem"]').click();
    assert(value === 'settings');
  });
});
