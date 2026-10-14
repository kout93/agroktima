/* Βελτιώσεις προσβασιμότητας: συσχέτιση label–πεδίου, τρέχουσα σελίδα στο μενού,
   κλείσιμο του «Περισσότερα». */
(function () {
  // 1. Κάθε <label> χωρίς for συνδέεται με το πεδίο που ακολουθεί (ή περιέχει).
  var n = 0;
  document.querySelectorAll('label:not([for])').forEach(function (label) {
    var ctl = label.querySelector('input,select,textarea');
    var next = label.nextElementSibling;
    while (!ctl && next && next.tagName !== 'LABEL') {
      if (/^(INPUT|SELECT|TEXTAREA)$/.test(next.tagName) && next.type !== 'hidden') { ctl = next; break; }
      var inner = next.querySelector && next.querySelector('input:not([type=hidden]),select,textarea');
      if (inner) { ctl = inner; break; }
      next = next.nextElementSibling;
    }
    if (!ctl || label.contains(ctl)) return;
    if (!ctl.id) ctl.id = 'f-' + (++n);
    label.setAttribute('for', ctl.id);
  });

  // 2. Τρέχουσα σελίδα στο μενού.
  var path = location.pathname;
  document.querySelectorAll('nav .links a[href]').forEach(function (a) {
    if (a.closest('.lang-switch')) return;
    var h = a.getAttribute('href');
    if (h === path || (h.length > 1 && path.indexOf(h) === 0)) {
      a.setAttribute('aria-current', 'page');
      var d = a.closest('details'); if (d) d.classList.add('has-current');
    }
  });

  // 3. «Περισσότερα»: κλείνει με Escape ή κλικ έξω.
  var more = document.querySelector('details.more');
  if (more) {
    document.addEventListener('click', function (e) { if (!more.contains(e.target)) more.removeAttribute('open'); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && more.hasAttribute('open')) { more.removeAttribute('open'); more.querySelector('summary').focus(); }
    });
  }
})();
