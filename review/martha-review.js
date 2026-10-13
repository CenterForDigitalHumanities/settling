// Martha archive review application logic — lightbox + off-the-record drawer.
// Loaded with `defer` on both review/martha.html and review/martha-audit.html.
// Expects `window.__MARTHA__` to be defined on the page (imageFilenames per doc, etc.)

const MarthaReview = (() => {
  // Base-relative to the site's `<base href="/">`. On local file:// the
  // inline base-rewrite sets the base to the site root, so this resolves the same
  // way as when served.
  const IMG_BASE = "review/martha/images/"
  const STORAGE_KEY = "martha-off-the-record"

  // ---------- Off-the-record store ----------
  const loadRedacted = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return {}
      const parsed = JSON.parse(raw)
      return parsed && typeof parsed === "object" ? parsed : {}
    } catch {
      return {}
    }
  }

  const saveRedacted = (store) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
    } catch { /* noop */ }
  }

  const onRedactedChanged = (store) => {
    document.dispatchEvent(new CustomEvent("martha:redacted-changed", { detail: store }))
  }

  const setRedacted = (docId, value) => {
    const store = loadRedacted()
    if (value) {
      store[docId] = true
    } else {
      delete store[docId]
    }
    saveRedacted(store)
    return store
  }

  const isRedacted = (docId) => Boolean(loadRedacted()[docId])
  const redactedIds = () => Object.keys(loadRedacted()).filter((k) => loadRedacted()[k])

  // Toggle control wiring: any element with [data-mark-otr="DOC-xxx"] toggles its doc.
  function syncOtrButtons() {
    document.querySelectorAll("[data-mark-otr]").forEach((btn) => {
      const id = btn.getAttribute("data-mark-otr")
      const active = isRedacted(id)
      btn.classList.toggle("is-redacted", active)
      btn.setAttribute("aria-pressed", active ? "true" : "false")
    })
  }

  function wireOtrButtons() {
    document.querySelectorAll("[data-mark-otr]").forEach((btn) => {
      if (btn.dataset.wired) return
      btn.dataset.wired = "1"
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-mark-otr")
        const next = !isRedacted(id)
        const store = setRedacted(id, next)
        syncOtrButtons()
        onRedactedChanged(store)
      })
    })
  }

  // ---------- Drawer ----------
  function buildDrawer() {
    if (document.getElementById("martha-otr-drawer")) return
    const drawer = document.createElement("div")
    drawer.id = "martha-otr-drawer"
    drawer.className = "martha-otr-drawer"
    drawer.setAttribute("aria-hidden", "true")
    drawer.innerHTML = `
      <div class="martha-drawer-head">
        <strong>Off the record</strong>
        <button class="martha-drawer-close" aria-label="Close drawer">×</button>
      </div>
      <p class="martha-drawer-hint">Documents marked off the record are listed here. Copy the list to send to the author.</p>
      <ul class="martha-drawer-list"></ul>
      <button class="martha-drawer-copy">Copy list to clipboard</button>
    `
    document.body.appendChild(drawer)
    drawer.querySelector(".martha-drawer-close").addEventListener("click", () => setDrawerOpen(false))
    drawer.querySelector(".martha-drawer-copy").addEventListener("click", copyListToClipboard)
  }

  function setDrawerOpen(open) {
    const drawer = document.getElementById("martha-otr-drawer")
    if (!drawer) return
    drawer.classList.toggle("is-open", open)
    drawer.setAttribute("aria-hidden", open ? "false" : "true")
  }

  function renderDrawerList(store) {
    const drawer = document.getElementById("martha-otr-drawer")
    if (!drawer) return
    const ul = drawer.querySelector(".martha-drawer-list")
    const registry = window.__MARTHA__?.documents || []
    const entries = Object.keys(store).filter((k) => store[k])
    if (!entries.length) {
      ul.innerHTML = '<li class="martha-drawer-empty">Nothing marked off the record yet.</li>'
      return
    }
    ul.innerHTML = entries.map((id) => {
      const doc = registry.find((d) => d.docId === id)
      const label = doc ? doc.title : id
      return `<li data-redact-id="${id}">
        <span class="martha-drawer-item-label">${escapeHtml(label)}</span>
        <button class="martha-drawer-remove" aria-label="Remove ${escapeHtml(label)}">×</button>
      </li>`
    }).join("")
    ul.querySelectorAll(".martha-drawer-remove").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.closest("li").getAttribute("data-redact-id")
        const store2 = setRedacted(id, false)
        syncOtrButtons()
        renderDrawerList(store2)
        onRedactedChanged(store2)
      })
    })
  }

  function copyListToClipboard() {
    const store = loadRedacted()
    const registry = window.__MARTHA__?.documents || []
    const entries = Object.keys(store).filter((k) => store[k])
    const lines = entries.map((id) => {
      const doc = registry.find((d) => d.docId === id)
      return doc ? `[${doc.docId}] ${doc.title}` : id
    })
    const body = [
      "Documents marked OFF THE RECORD (Martha M. Hamilton archive):",
      "",
      ...lines,
      "",
      "— Please exclude these from any published version.",
    ].join("\n")
    const write = (text) => {
      const ta = document.createElement("textarea")
      ta.value = text
      ta.setAttribute("readonly", "")
      ta.style.position = "fixed"
      ta.style.opacity = "0"
      document.body.appendChild(ta)
      ta.focus()
      ta.select()
      let ok = false
      try {
        ok = document.execCommand("copy")
      } catch {
        ok = false
      }
      document.body.removeChild(ta)
      return ok
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(body).then(
        () => flashCopy(true),
        () => flashCopy(write(body))
      )
    } else {
      flashCopy(write(body))
    }
  }

  function flashCopy(ok) {
    const btn = document.querySelector(".martha-drawer-copy")
    if (!btn) return
    const prev = btn.textContent
    btn.textContent = ok ? "✓ Copied" : "Copy failed"
    btn.classList.toggle("is-copied", ok)
    setTimeout(() => {
      btn.textContent = prev
      btn.classList.remove("is-copied")
    }, 1800)
  }

  // ---------- Lightbox ----------
  function buildLightbox() {
    if (document.getElementById("martha-lightbox")) return
    const lb = document.createElement("div")
    lb.id = "martha-lightbox"
    lb.className = "martha-lightbox"
    lb.setAttribute("aria-hidden", "true")
    lb.innerHTML = `
      <div class="martha-lightbox-backdrop"></div>
      <div class="martha-lightbox-body">
        <div class="martha-lightbox-toolbar">
          <span class="martha-lightbox-title"></span>
          <span class="martha-lightbox-count"></span>
          <button class="martha-lightbox-close" aria-label="Close">×</button>
        </div>
        <div class="martha-lightbox-viewport">
          <button class="martha-lightbox-nav prev" aria-label="Previous page">‹</button>
          <img class="martha-lightbox-img" alt="">
          <button class="martha-lightbox-nav next" aria-label="Next page">›</button>
        </div>
        <div class="martha-lightbox-caption"></div>
      </div>
    `
    document.body.appendChild(lb)
    lb.querySelector(".martha-lightbox-backdrop").addEventListener("click", closeLightbox)
    lb.querySelector(".martha-lightbox-close").addEventListener("click", closeLightbox)
    lb.querySelector(".martha-lightbox-nav.prev").addEventListener("click", () => navLightbox(-1))
    lb.querySelector(".martha-lightbox-nav.next").addEventListener("click", () => navLightbox(1))
    document.addEventListener("keydown", (e) => {
      if (lightboxState.open) {
        if (e.key === "Escape") closeLightbox()
        if (e.key === "ArrowLeft") navLightbox(-1)
        if (e.key === "ArrowRight") navLightbox(1)
      }
    })
  }

  const lightboxState = { open: false, index: 0, pages: [] }

  function openLightbox(pages, index = 0) {
    buildLightbox()
    const lb = document.getElementById("martha-lightbox")
    lightboxState.pages = pages
    lightboxState.index = index
    renderLightbox(lb)
    lb.classList.add("is-open")
    lb.setAttribute("aria-hidden", "false")
    lightboxState.open = true
    document.body.classList.add("martha-lightbox-locked")
  }

  function closeLightbox() {
    const lb = document.getElementById("martha-lightbox")
    if (!lb) return
    lb.classList.remove("is-open")
    lb.setAttribute("aria-hidden", "true")
    lightboxState.open = false
    document.body.classList.remove("martha-lightbox-locked")
  }

  function navLightbox(delta) {
    const lb = document.getElementById("martha-lightbox")
    if (!lb || !lightboxState.pages.length) return
    const nextIndex = lightboxState.index + delta
    if (nextIndex < 0 || nextIndex >= lightboxState.pages.length) return
    lightboxState.index = nextIndex
    renderLightbox(lb)
  }

  function renderLightbox(lb) {
    const { pages, index } = lightboxState
    const page = pages[index]
    if (!page) return
    const title = lb.querySelector(".martha-lightbox-title")
    const img = lb.querySelector(".martha-lightbox-img")
    const count = lb.querySelector(".martha-lightbox-count")
    const caption = lb.querySelector(".martha-lightbox-caption")
    const prevBtn = lb.querySelector(".martha-lightbox-nav.prev")
    const nextBtn = lb.querySelector(".martha-lightbox-nav.next")
    title.textContent = page.label || ""
    img.src = IMG_BASE + encodeURIComponent(page.imageFile)
    img.alt = page.label || "Document page"
    // Apply the natural reading rotation so sideways scans display upright.
    const rot = page.rotation || 0
    img.style.transform = rot ? `rotate(${rot}deg)` : ""
    img.classList.toggle("is-rotated", Boolean(rot))
    count.textContent = `${index + 1} / ${pages.length}`
    caption.textContent = page.imageFile
    // Hide navigation arrows when they are not operable: a single image, or at
    // the ends of a set (no wrapping).
    prevBtn.classList.toggle("is-hidden", pages.length <= 1 || index === 0)
    nextBtn.classList.toggle("is-hidden", pages.length <= 1 || index === pages.length - 1)
  }

  // Wire thumbnails / preview buttons that hold [data-open-lightbox]
  function wireLightboxTriggers() {
    document.querySelectorAll("[data-open-lightbox]").forEach((el) => {
      if (el.dataset.wired) return
      el.dataset.wired = "1"
      el.addEventListener("click", (e) => {
        e.preventDefault()
        const docId = el.getAttribute("data-open-lightbox")
        const doc = (window.__MARTHA__?.documents || []).find((d) => d.docId === docId)
        if (!doc) return
        const pages = (doc.pages || []).map((p) => ({
          imageFile: p.imageFile,
          rotation: p.rotation || 0,
          pageNumber: p.pageNumber,
          label: `${doc.docId} — ${doc.title} · p. ${p.pageNumber}`,
        }))
        if (!pages.length) return
        // Optional 1-based page number so a per-page thumbnail opens on that page.
        const want = parseInt(el.getAttribute("data-open-page"), 10)
        const at = Number.isNaN(want) ? 0 : pages.findIndex((p) => p.pageNumber === want)
        openLightbox(pages, at < 0 ? 0 : at)
      })
    })
  }

  const escapeHtml = (s) =>
    (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;")

  function init() {
    buildLightbox()
    // The off-the-record drawer is only used on the audit page. Enable it only
    // when the page actually renders OTR buttons, so the report page stays clean.
    const hasOtr = document.querySelectorAll("[data-mark-otr]").length > 0
    if (hasOtr) {
      buildDrawer()
      wireOtrButtons()
      syncOtrButtons()
      renderDrawerList(loadRedacted())
      // Floating toggle for the drawer
      if (!document.getElementById("martha-drawer-toggle")) {
        const toggle = document.createElement("button")
        toggle.id = "martha-drawer-toggle"
        toggle.className = "martha-drawer-toggle"
        toggle.textContent = "Off the record"
        toggle.addEventListener("click", () => {
          const drawer = document.getElementById("martha-otr-drawer")
          setDrawerOpen(!drawer.classList.contains("is-open"))
        })
        document.body.appendChild(toggle)
      }
    }
    wireLightboxTriggers()
    document.addEventListener("martha:redacted-changed", (e) => renderDrawerList(e.detail))
    // Re-sync buttons after any dynamic DOM insert
    const mo = new MutationObserver(() => {
      if (hasOtr) {
        wireOtrButtons()
        syncOtrButtons()
      }
      wireLightboxTriggers()
    })
    mo.observe(document.body, { childList: true, subtree: true })
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init)
  } else {
    init()
  }

  return { init, openLightbox, closeLightbox, setRedacted, isRedacted }
})()
