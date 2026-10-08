/* Εναλλαγή σκοτεινού φόντου για ξεκούραση ματιών (ιδιαίτερα το βράδυ).
   Η επιλογή απομνημονεύεται στο localStorage της συσκευής. */
(function () {
  var STORAGE_KEY = 'agroktima-theme';
  var btn = document.getElementById('theme-toggle');
  var icon = document.getElementById('theme-toggle-icon');
  if (!btn || !icon) return;

  function current() {
    return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  function render() {
    // Όταν είμαστε ήδη σε σκοτεινό φόντο, δείξε ήλιο (πάτα για να γυρίσεις σε φωτεινό).
    // Όταν είμαστε σε φωτεινό φόντο, δείξε μισοφέγγαρο (πάτα για να πας σε σκοτεινό).
    icon.textContent = current() === 'dark' ? '☀️' : '🌙';
  }

  btn.addEventListener('click', function () {
    var next = current() === 'dark' ? 'light' : 'dark';
    if (next === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    try { localStorage.setItem(STORAGE_KEY, next); } catch (e) {}
    render();
  });

  render();
})();
