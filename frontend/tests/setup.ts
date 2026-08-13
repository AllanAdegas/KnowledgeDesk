import '@testing-library/jest-dom/vitest'

// jsdom does not implement scrollIntoView; ChatWindow relies on it to
// auto-scroll on new messages, so provide a harmless no-op for tests.
if (!HTMLElement.prototype.scrollIntoView) {
  HTMLElement.prototype.scrollIntoView = () => {}
}
