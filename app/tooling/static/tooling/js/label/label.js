document.addEventListener("DOMContentLoaded", function() {
    // Select all alert messages
    const alerts = document.querySelectorAll('.alert');

    // Loop through each alert message
    alerts.forEach(alert => {
        // If the alert has the class 'alert-success'
        if (alert.classList.contains('alert-success')) {
            // Set a timeout to hide the alert after 1 second
            setTimeout(function() {
                alert.style.display = 'none';
            }, 1000); // 1 second
        }
    });
});
