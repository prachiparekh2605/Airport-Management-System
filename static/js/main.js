/**
 * Airport Staff Management System - Core Frontend Script
 * Professional Operations HUD & Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile sidebar toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('show');
    });
  }

  // 2. Real-Time Airport Operations Clock (Local & UTC)
  initAirportClock();

  // 3. Universal Table Search Filter
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

  // 4. Global Keyboard Shortcut: Press '/' to focus table search
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
      const firstSearch = document.querySelector('.table-search-input');
      if (firstSearch) {
        e.preventDefault();
        firstSearch.focus();
        firstSearch.select();
      }
    }
  });

  // 5. Auto-dismiss alerts after 5 seconds
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
 * Real-Time Airport Operations Digital Clock
 */
function initAirportClock() {
  const localEl = document.getElementById('opsClockLocal');
  const utcEl = document.getElementById('opsClockUTC');
  if (!localEl && !utcEl) return;

  function updateClock() {
    const now = new Date();

    if (localEl) {
      const hours = String(now.getHours()).padStart(2, '0');
      const mins = String(now.getMinutes()).padStart(2, '0');
      const secs = String(now.getSeconds()).padStart(2, '0');
      localEl.textContent = `${hours}:${mins}:${secs} LOC`;
    }

    if (utcEl) {
      const uHours = String(now.getUTCHours()).padStart(2, '0');
      const uMins = String(now.getUTCMinutes()).padStart(2, '0');
      const uSecs = String(now.getUTCSeconds()).padStart(2, '0');
      utcEl.textContent = `${uHours}:${uMins}:${uSecs} UTC`;
    }
  }

  updateClock();
  setInterval(updateClock, 1000);
}

/**
 * Universal CSV Export for Tables
 * Exports table data cleanly into downloadable .csv file
 */
function exportTableToCSV(tableId, filename) {
  const table = document.getElementById(tableId);
  if (!table) return;

  let csvContent = "";
  const rows = table.querySelectorAll("tr");

  rows.forEach(row => {
    // Skip hidden rows or no-results row
    if (row.style.display === 'none' || row.classList.contains('no-results-row')) return;

    const cols = row.querySelectorAll("th, td");
    const rowData = [];

    cols.forEach((col, index) => {
      // Skip the last "Actions" column if it contains buttons
      if (index === cols.length - 1 && (col.querySelector('button') || col.textContent.trim().toLowerCase().includes('action'))) {
        return;
      }
      // Clean string
      let text = col.innerText.replace(/(\r\n|\n|\r)/gm, " ").trim();
      text = text.replace(/"/g, '""'); // escape double quotes
      rowData.push(`"${text}"`);
    });

    if (rowData.length > 0) {
      csvContent += rowData.join(",") + "\r\n";
    }
  });

  // Download trigger
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", (filename || "airport_data") + "_" + new Date().toISOString().slice(0, 10) + ".csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Print function for Boarding Pass
 */
function printPass() {
  window.print();
}

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
