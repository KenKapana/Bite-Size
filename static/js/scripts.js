document.addEventListener("DOMContentLoaded", function () {
  function check_update_success() {
    fetch("/check_update_success")
      .then((response) => response.json())
      .then((data) => {
        if (data.update_successful) {
          alert("Hours updated successfully!");
        }
      });
  }

  function toggle_dropdown() {
    const dropdownToggle = document.querySelector(".dropdown_toggle");
    const dropdownContent = document.querySelector(".dropdown_content");
    
    dropdownToggle.addEventListener('click', () => {
      dropdownContent.classList.toggle('show');
    });

    window.addEventListener('click', (event) => {
      if (!event.target.matches('.dropdown_toggle')) {
        if (dropdownContent.classList.contains('show')) {
          dropdownContent.classList.remove('show');
        }
      }
    });
  }

  // Set the welcome message in the element with id "welcome_message"
  const welcomeMessage = `Welcome to bite size! 🎉<br>
    Hey there, go-getter! Welcome to bite size, where we turn your to-do lists into "done" lists. 
    Say goodbye to procrastination and hello to productivity! 🗓️✨
    
    With bite size, you can effortlessly schedule your tasks and watch as we organize your day like a pro. 
    No more excuses, just seamless scheduling and sweet, sweet accomplishment. 
    Let's get those tasks tackled, one awesome day at a time. Ready to conquer your schedule? Let's go! 🚀💪`;

  const welcomeElement = document.getElementById("welcome_message");
  if (welcomeElement) {
    welcomeElement.innerHTML = welcomeMessage;
  }

  toggle_dropdown();
  check_update_success();

});
