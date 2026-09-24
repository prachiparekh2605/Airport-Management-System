/**
 * Airport Staff Management System - Core Frontend Script
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile sidebar toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('show');
    });
  }

  // Universal Table Search Filter
  const searchInputs = document.querySelectorAll('.table-search-input');
  searchInputs.forEach(input => {
    const tableId = input.getAttribute('data-table');
    const table = document.getElementById(tableId);
    if (!table) return;

    input.addEventListener('input', () => {
      const query = input.value.toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');
      let visibleCount = 0;

      rows.forEach(row => {
        // Skip empty placeholder rows if any
        if (row.classList.contains('no-results-row')) return;

        const text = row.textContent.toLowerCase();
        if (text.includes(query)) {
          row.style.display = '';
          visibleCount++;
        } else {
          row.style.display = 'none';
        }
      });

      // Handle no results indicator
      let noResult = table.querySelector('.no-results-row');
      if (visibleCount === 0 && rows.length > 0) {
        if (!noResult) {
          const colCount = table.querySelectorAll('thead th').length || 6;
          noResult = document.createElement('tr');
          noResult.className = 'no-results-row';
          noResult.innerHTML = `<td colspan="${colCount}" class="text-center py-4 text-muted">
            <i class="bi bi-search me-2"></i>No matching records found for "${input.value}"
          </td>`;
          table.querySelector('tbody').appendChild(noResult);
        } else {
          noResult.style.display = '';
        }
      } else if (noResult) {
        noResult.style.display = 'none';
      }
    });
  });

  // Auto-dismiss alerts after 5 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach(alert => {
    setTimeout(() => {
      if (window.bootstrap && bootstrap.Alert) {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      }
    }, 5000);
  });
});

/**
 * Helper to auto-fill login credentials from quick-access chips
 */
function fillLogin(username, password) {
  const userInput = document.getElementById('username');
  const passInput = document.getElementById('password');
  if (userInput && passInput) {
    userInput.value = username;
    passInput.value = password;
    userInput.focus();
  }
}

/**
 * Standard confirmation modal or prompt before deletion
 */
function confirmAction(message, callback) {
  if (confirm(message || 'Are you sure you want to delete this record? This action cannot be undone.')) {
    if (typeof callback === 'function') callback();
    return true;
  }
  return false;
}
