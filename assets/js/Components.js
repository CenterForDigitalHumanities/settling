window.SiteComponents = (function() {

  function getScriptDir() {
    var scripts = document.querySelectorAll("script[src*=\"Components.js\"]");
    if (scripts.length) {
      var src = scripts[scripts.length - 1].src;
      return src.substring(0, src.lastIndexOf("/") + 1);
    }
    return "assets/js/";
  }

  function cssPath() {
    return getScriptDir() + "../styles.css";
  }

  function navLinks(depth) {
    var links = [
      { label: "Archive",      href: depth + "archive/index.html" },
      { label: "Cases",        href: depth + "cases/index.html" },
      { label: "Oral Histories", href: depth + "oral-histories/index.html" },
      { label: "About",        href: depth + "about.html" },
      { label: "Contact",      href: depth + "contact.html" }
    ];
    return links;
  }

  function renderNav() {
    if (document.querySelector("nav.main-nav")) return;

    var currentPath = window.location.pathname;
    var depth = currentPath.split("/").filter(Boolean).length;
    var prefix = depth === 0 ? "" : "../".repeat(depth);

    var navLinks = [
      { label: "Archive",      path: prefix + "archive/index.html" },
      { label: "Cases",        path: prefix + "cases/index.html" },
      { label: "Oral Histories", path: prefix + "oral-histories/index.html" },
      { label: "Timeline",     path: prefix + "timeline.html" },
      { label: "About",        path: prefix + "about.html" },
      { label: "Contact",      path: prefix + "contact.html" }
    ];

    if (currentPath.includes("/oral-histories/")) {
      navLinks.unshift({ label: "Interviews", path: prefix + "oral-histories/interviews.html" });
    }

    var html = '<nav class="main-nav"><div class="container">';
    html += '<a href="' + prefix + 'index.html" class="nav-brand">Settling</a>';
    html += '<ul class="nav-links">';
    for (var i = 0; i < navLinks.length; i++) {
      html += '<li><a href="' + navLinks[i].path + '">' + navLinks[i].label + '</a></li>';
    }
    html += '</ul></div></nav>';

    document.body.insertAdjacentHTML("afterbegin", html);
  }

  function renderFooter() {
    if (document.querySelector("footer")) return;

    var html = '<footer><div class="container">';
    html += '<p>&copy; <span id="year"></span> Research Computing Group. All rights reserved.</p>';
    html += '<p class="footer-note">Forthcoming book by Dr. Ashley Walter, PhD</p>';
    html += '</div></footer>';

    document.body.insertAdjacentHTML("beforeend", html);
    document.getElementById("year").textContent = new Date().getFullYear();
  }

  return {
    renderNav: renderNav,
    renderFooter: renderFooter,
    renderAll: function() {
      renderNav();
      renderFooter();
    }
  };
})();

document.addEventListener("DOMContentLoaded", function() {
  SiteComponents.renderAll();
});
