/**
 * Amahirwe: progressive-enhancement replacement for native <select>
 * dropdowns.
 *
 * Why: a native <select>'s open popup (direction, colours, hover
 * state) is rendered by the OS/browser, not the page — no CSS can
 * control it, which is why it could flip open upward and show with
 * mismatched (usually purple) highlight colours. This builds a fully
 * custom, always-opens-downward dropdown in the site's own neumorphic
 * style instead.
 *
 * The real <select> is kept in the DOM (just visually hidden), same
 * id/name/value/options as before — every existing script elsewhere
 * in the app that does `select.value`, `form.field.value = x`,
 * `select.addEventListener("change", ...)`, or populates <option>s
 * after a fetch keeps working untouched. This module only replaces
 * how the control is displayed and interacted with; a MutationObserver
 * mirrors option/attribute changes made by that other code onto the
 * custom widget automatically, so no other file needs to know this
 * exists.
 */

function buildCustomSelect(select) {
  if (select.dataset.customSelectReady) return;
  select.dataset.customSelectReady = "true";

  const wrapper = document.createElement("div");
  wrapper.className = "custom-select";

  select.parentNode.insertBefore(wrapper, select);
  wrapper.appendChild(select);
  select.classList.add("custom-select__native");
  select.setAttribute("tabindex", "-1");
  select.setAttribute("aria-hidden", "true");

  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "custom-select__trigger";
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-expanded", "false");
  trigger.innerHTML =
    '<span class="custom-select__value"></span>' +
    '<svg class="custom-select__chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';

  const list = document.createElement("ul");
  list.className = "custom-select__list";
  list.setAttribute("role", "listbox");
  list.hidden = true;

  wrapper.appendChild(trigger);
  wrapper.appendChild(list);

  // Selects populated dynamically (e.g. a school list fetched after
  // page load) start with no id-based label association issue since
  // the <label for="..."> still points at the (now hidden) native
  // select; redirect its click to the visible trigger instead.
  if (select.id) {
    const label = document.querySelector(`label[for="${select.id}"]`);
    if (label) {
      label.addEventListener("click", (e) => {
        e.preventDefault();
        trigger.focus();
      });
    }
  }

  function renderOptions() {
    list.innerHTML = "";
    Array.from(select.options).forEach((opt, i) => {
      const li = document.createElement("li");
      li.setAttribute("role", "option");
      li.dataset.index = String(i);
      li.textContent = opt.textContent;
      li.className = "custom-select__option";
      if (opt.disabled) {
        li.setAttribute("aria-disabled", "true");
        li.classList.add("is-disabled");
      }
      list.appendChild(li);
    });
    syncDisplay();
  }

  function syncDisplay() {
    const selected = select.options[select.selectedIndex];
    trigger.querySelector(".custom-select__value").textContent = selected ? selected.textContent : "";
    list.querySelectorAll(".custom-select__option").forEach((li) => {
      const isSelected = li.dataset.index === String(select.selectedIndex);
      li.setAttribute("aria-selected", String(isSelected));
      li.classList.toggle("is-selected", isSelected);
    });
    wrapper.classList.toggle("is-disabled", select.disabled);
    wrapper.classList.toggle("has-error", select.classList.contains("has-error"));
  }

  function setActive(options, idx) {
    options.forEach((o) => o.classList.remove("is-active"));
    if (options[idx]) {
      options[idx].classList.add("is-active");
      options[idx].scrollIntoView({ block: "nearest" });
    }
  }

  function openList() {
    if (select.disabled || select.options.length === 0) return;
    list.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    wrapper.classList.add("is-open");
    const options = Array.from(list.querySelectorAll(".custom-select__option"));
    const startIdx = select.selectedIndex >= 0 ? select.selectedIndex : 0;
    setActive(options, startIdx);
    document.addEventListener("click", onDocClick);
    document.addEventListener("keydown", onListKeydown);
  }

  function closeList() {
    list.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
    wrapper.classList.remove("is-open");
    list.querySelectorAll(".is-active").forEach((el) => el.classList.remove("is-active"));
    document.removeEventListener("click", onDocClick);
    document.removeEventListener("keydown", onListKeydown);
  }

  function onDocClick(e) {
    if (!wrapper.contains(e.target)) closeList();
  }

  function selectOption(li) {
    if (li.classList.contains("is-disabled")) return;
    const idx = Number(li.dataset.index);
    if (select.selectedIndex !== idx) {
      select.selectedIndex = idx;
      select.dispatchEvent(new Event("change", { bubbles: true }));
    }
    syncDisplay();
    closeList();
    trigger.focus();
  }

  function onListKeydown(e) {
    const options = Array.from(list.querySelectorAll(".custom-select__option"));
    const activeEl = list.querySelector(".is-active");
    let idx = activeEl ? options.indexOf(activeEl) : -1;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive(options, Math.min(options.length - 1, idx + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive(options, Math.max(0, idx - 1));
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (activeEl) selectOption(activeEl);
    } else if (e.key === "Escape" || e.key === "Tab") {
      closeList();
      if (e.key === "Escape") trigger.focus();
    }
  }

  trigger.addEventListener("click", () => {
    if (list.hidden) openList();
    else closeList();
  });

  trigger.addEventListener("keydown", (e) => {
    if (list.hidden && (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      openList();
    }
  });

  list.addEventListener("click", (e) => {
    const li = e.target.closest(".custom-select__option");
    if (li) selectOption(li);
  });

  // Reflect changes other scripts make directly to the native select
  // (new <option>s after a fetch, an option's label changing on a
  // language switch, a toggled "has-error"/disabled state) onto the
  // custom widget, without those scripts needing to know this
  // enhancement exists. subtree+characterData is what catches a
  // language switch specifically: applyTranslations() rewrites each
  // <option>'s text node in place, it doesn't add/remove <option>
  // elements, so childList alone would miss it.
  new MutationObserver((mutations) => {
    const structural = mutations.some((m) => m.type === "childList" || m.type === "characterData");
    if (structural) renderOptions();
    else syncDisplay();
  }).observe(select, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: ["class", "disabled"],
  });

  // Programmatic `select.value = x` (used throughout the app to
  // pre-fill a form from fetched data) doesn't fire a "change" event,
  // so a plain listener would miss it — poll instead. Cheap: a handful
  // of selects, a string comparison every 200ms.
  let lastValue = select.value;
  setInterval(() => {
    if (select.value !== lastValue) {
      lastValue = select.value;
      syncDisplay();
    }
  }, 200);

  select.addEventListener("change", () => {
    lastValue = select.value;
    syncDisplay();
  });

  renderOptions();
}

function initCustomSelects(root = document) {
  root.querySelectorAll(".form-select").forEach(buildCustomSelect);
}

export { initCustomSelects };
