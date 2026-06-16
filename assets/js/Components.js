const SiteComponents = (() => {
  const RELEASE_DATE = new Date("2026-10-28T00:00:00").getTime()

  const prefixFor = () => {
    // All relative URLs are resolved from /settling/ by <base href="/settling/">
    return ""
  }

  class SettlingNav extends HTMLElement {
    connectedCallback() {
      const prefix = prefixFor()
      const currentPath = window.location.pathname

      const links = [
        { label: "Archive",        path: prefix + "archive/index.html" },
        { label: "Cases",          path: prefix + "cases/index.html" },
        { label: "Oral Histories", path: prefix + "oral-histories/index.html" },
        { label: "Timeline",       path: prefix + "timeline.html" },
        { label: "About",          path: prefix + "about.html" },
        { label: "Contact",        path: prefix + "contact.html" }
      ]

      if (currentPath.includes("/oral-histories/")) {
        links.unshift({ label: "Interviews", path: prefix + "oral-histories/interviews.html" })
      }

      this.innerHTML = `
        <nav class="main-nav"><div class="container">
          <a href="${prefix}index.html" class="nav-brand">Settling</a>
          <ul class="nav-links">
            ${links.map(l => `<li><a href="${l.path}">${l.label}</a></li>`).join("")}
          </ul>
        </div></nav>`
    }
  }

  class SettlingReleaseBanner extends HTMLElement {
    constructor() {
      super()
      this._intervalId = null
    }

    connectedCallback() {
      const prefix = prefixFor()

      this.innerHTML = `
        <div class="release-banner"><div class="container">
          <div class="release-banner-book"><img src="${prefix}assets/settling-book.png" alt="Settling book cover"></div>
          <span class="release-banner-text">
            <strong>Coming October 28, 2026</strong> — <em>Settling: Women Who Sued the News</em> by Dr. Ashley Walter
            <span id="release-countdown"></span>
          </span>
          <button class="release-banner-close" aria-label="Dismiss banner">&times;</button>
        </div></div>`

      this._setupDismiss()
      this._restoreDismissed()
      this._startCountdown()
    }

    disconnectedCallback() {
      if (this._intervalId) clearInterval(this._intervalId)
    }

    _setupDismiss() {
      const closeBtn = this.querySelector(".release-banner-close")
      closeBtn?.addEventListener("click", () => {
        this._dismiss()
        try { localStorage.setItem("release-banner-dismissed", "true") } catch { /* noop */ }
      })
    }

    _restoreDismissed() {
      try {
        if (localStorage.getItem("release-banner-dismissed") === "true") {
          this._dismiss()
        }
      } catch { /* noop */ }
    }

    _dismiss() {
      const banner = this.querySelector(".release-banner")
      banner?.style.setProperty("display", "none")
    }

    _startCountdown() {
      this._updateCountdown()
      this._intervalId = setInterval(() => this._updateCountdown(), 1000)
    }

    _updateCountdown() {
      const el = this.querySelector("#release-countdown")
      if (!el) return

      const diff = RELEASE_DATE - Date.now()

      if (diff <= 0) {
        el.textContent = "— Available now!"
        return
      }

      const totalDays = Math.floor(diff / 86400000)
      const totalWeeks = Math.floor(totalDays / 7)
      const totalMonths = Math.floor(totalDays / 30)
      const hours = Math.floor((diff % 86400000) / 3600000)

      let text
      if (totalMonths >= 2) {
        text = `${totalMonths} ${totalMonths === 1 ? "month" : "months"} to go`
      } else if (totalWeeks >= 2) {
        text = `${totalWeeks} ${totalWeeks === 1 ? "week" : "weeks"} to go`
      } else {
        text = `${totalDays} ${totalDays === 1 ? "day" : "days"}${totalDays < 2 ? ` ${hours}h` : ""} to go`
      }

      el.textContent = `— ${text}`
    }
  }

  class SettlingFooter extends HTMLElement {
    connectedCallback() {
      this.innerHTML = `
        <footer><div class="container">
          <p>&copy; <span id="year"></span> Research Computing Group. All rights reserved.</p>
          <p class="footer-note">"Settling: Women Who Sued the News" by Dr. Ashley Walter — October 28, 2026</p>
        </div></footer>`

      this.querySelector("#year").textContent = new Date().getFullYear()
    }
  }

  customElements.define("settling-nav", SettlingNav)
  customElements.define("settling-release-banner", SettlingReleaseBanner)
  customElements.define("settling-footer", SettlingFooter)

  return { SettlingNav, SettlingReleaseBanner, SettlingFooter }
})()
