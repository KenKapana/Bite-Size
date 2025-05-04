function toggleHour(element) {
  element.classList.toggle("selected");
  const checkbox = element.querySelector('input[type="checkbox"]');
  checkbox.checked = !checkbox.checked;
}

// Check for success message
window.onload = function () {
  fetch('{{ url_for("calendar.check_update_success") }}')
    .then((response) => response.json())
    .then((data) => {
      if (data.update_successful) {
        showNotification("Hours updated successfully!");
      }
    });
};

function showNotification(message) {
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.classList.add('show');
  }, 100);
  
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}