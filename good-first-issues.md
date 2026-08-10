# 🎯 Good First Issues & Community Roadmap (`@universal-ui/engine`)

Welcome contributors! Below is our curated roadmap of upcoming Web Component primitives. Each issue details the required tag name, exact functional specification, CSS tokens to inherit, and Custom Events to emit.

---

## 📌 Issue #1: `<universal-toast>` Overlay Notification Manager

* **Title**: `[Feature]: Implement <universal-toast> global notification alert manager`
* **Labels**: `good first issue`, `enhancement`, `help wanted`, `hacktoberfest`

### 📋 Description & Implementation Scope
Build a fixed viewport notification manager component that listens for global or programmatic alert events and renders auto-dismissing toast popups in the top-right or bottom-right corner.

### 📐 Component Contract Matrix

* **Tag Name**: `<universal-toast>`
* **Observed Attributes**: `position` (`top-right` | `top-left` | `bottom-right` | `bottom-left`), `duration` (number in ms, default `4000`)
* **Properties**:
  * `toasts` (Array): Array of `{ id, type: 'success'|'danger'|'warning'|'info', title, message, duration }`
* **Public Methods**:
  * `showToast({ type, title, message, duration })`: Appends a toast to active list.
  * `clearAll()`: Removes all active toast popups immediately.
* **Custom Events Emitted**:
  * `toast-dismiss`: Emitted when a toast is closed manually or via timer expiry. `e.detail = { toastId, type }`

### 🎨 Required Theme Token Inheritance
* Backgrounds: `var(--color-bg-surface)`
* Text: `var(--color-text-primary)`
* Status Accents: `var(--color-success)`, `var(--color-danger)`, `var(--color-warning)`, `var(--color-primary)`
* Shadow & Border: `var(--shadow-lg)`, `var(--color-border)`

---

## 📌 Issue #2: `<universal-modal-dialog>` Accessible Modal Container

* **Title**: `[Feature]: Implement accessible <universal-modal-dialog> with keyboard trapping`
* **Labels**: `good first issue`, `accessibility`, `enhancement`

### 📋 Description & Implementation Scope
Create an accessible modal overlay dialog box that locks body scrolling, traps keyboard `Tab` focus within the active dialog, handles `Escape` key dismissal, and exposes customizable header, body, and footer slots.

### 📐 Component Contract Matrix

* **Tag Name**: `<universal-modal-dialog>`
* **Observed Attributes**: `open` (boolean attribute), `title` (string header), `size` (`sm` | `md` | `lg`)
* **Slots**:
  * `header`: Custom title header replace slot
  * `default`: Main modal body content
  * `footer`: Action buttons slot (e.g. Confirm, Cancel)
* **Public Methods**:
  * `open()`: Displays modal dialog and traps keyboard focus.
  * `close()`: Closes modal dialog and restores document scroll focus.
* **Custom Events Emitted**:
  * `modal-open`: Emitted when modal opens. `e.detail = { timestamp }`
  * `modal-close`: Emitted when modal closes via backdrop click, ESC key, or close button. `e.detail = { reason: 'backdrop'|'escape'|'button' }`

### 🎨 Required Theme Token Inheritance
* Backdrop: `rgba(0, 0, 0, 0.5)` with `backdrop-filter: blur(4px)`
* Container: `var(--color-bg-surface)`, `var(--radius-lg)`, `var(--shadow-xl)`
* Header & Border: `var(--color-border)`, `var(--font-weight-bold)`

---

## 📌 Issue #3: `<universal-badge-cloud>` Metadata Tag Grouping System

* **Title**: `[Feature]: Implement <universal-badge-cloud> with deletion and add triggers`
* **Labels**: `good first issue`, `enhancement`, `ui`

### 📋 Description & Implementation Scope
Develop a responsive badge cloud/chip grouping component capable of displaying categorized tags, filtering metadata, and supporting removable tags with deletion events and input field addition.

### 📐 Component Contract Matrix

* **Tag Name**: `<universal-badge-cloud>`
* **Observed Attributes**: `removable` (boolean attribute), `variant` (`default` | `primary` | `outline`)
* **Properties**:
  * `tags` (Array | JSON string): `["JavaScript", "Web Components", "Shadow DOM", "ES6"]` or array of `{ id, label, color }`
* **Custom Events Emitted**:
  * `tag-remove`: Emitted when the close (`×`) icon on a tag is clicked. `e.detail = { removedTag, remainingTags: Array }`
  * `tag-click`: Emitted when a tag item is clicked. `e.detail = { tag }`

### 🎨 Required Theme Token Inheritance
* Badges: `var(--color-primary-light)`, `var(--color-primary)`, `var(--radius-full)`
* Typography: `var(--font-size-xs)`, `var(--font-weight-medium)`
* Transitions: `var(--transition-fast)`

---

## 🚀 How to Claim an Issue

1. Comment on the respective GitHub Issue stating you'd like to work on it.
2. Review `CONTRIBUTING.md` and use `elements/template-primitive.js` as your boilerplate.
3. Submit a Pull Request referencing the Issue number!
