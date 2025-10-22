(function () {
  const sidebar = document.querySelector('.admin-sidebar');
  const toggleBtn = document.getElementById('sidebarToggle');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }

  const themeBtn = document.getElementById('toggleThemeBtn');
  const html = document.documentElement;
  function setTheme(next) {
    html.setAttribute('data-bs-theme', next);
    try { localStorage.setItem('fieldnote-theme', next); } catch (_) {}
  }
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const cur = html.getAttribute('data-bs-theme') || 'light';
      setTheme(cur === 'light' ? 'dark' : 'light');
    });
  }
  try {
    const saved = localStorage.getItem('fieldnote-theme');
    if (saved) setTheme(saved);
  } catch (_) {}
})();
