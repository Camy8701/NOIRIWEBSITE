(() => {
  const NOTICE_ATTR = "data-local-form-notice";
  const HANDLER_ATTR = "data-local-form-handler";

  function ensureNotice(form) {
    let notice = form.querySelector(`[${NOTICE_ATTR}]`);
    if (notice) return notice;

    notice = document.createElement("div");
    notice.setAttribute(NOTICE_ATTR, "true");
    notice.hidden = true;
    notice.style.marginTop = "16px";
    notice.style.padding = "14px 18px";
    notice.style.border = "1px solid var(--token-dcae5064-f2b3-4dec-a44c-68dbb4450cfb, rgba(248,248,248,0.25))";
    notice.style.background = "rgba(248,248,248,0.06)";
    notice.style.color = "var(--token-43d9b09c-4aaa-49ce-8e2e-f50a4e46d8e9, #f8f8f8)";
    notice.style.fontSize = "14px";
    notice.style.lineHeight = "1.4";
    form.appendChild(notice);
    return notice;
  }

  function handleSubmit(form, event) {
    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    const notice = ensureNotice(form);
    event.preventDefault();
    event.stopImmediatePropagation();

    const data = new FormData(form);
    const rawName = String(data.get("Name") || "").trim();
    const name = rawName || "there";

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.setAttribute("aria-busy", "true");
    }

    window.setTimeout(() => {
      notice.hidden = false;
      notice.textContent = `Thanks, ${name}. This standalone replica uses a local contact stub, so the message is saved only in your browser session and is not sent to a remote backend.`;
      form.dataset.localSubmitted = "true";

      if (submitButton) {
        submitButton.disabled = false;
        submitButton.removeAttribute("aria-busy");
      }
    }, 160);
  }

  if (window[HANDLER_ATTR]) return;
  window[HANDLER_ATTR] = true;

  document.addEventListener(
    "submit",
    (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;
      handleSubmit(form, event);
    },
    true
  );
})();
