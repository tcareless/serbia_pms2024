function printLabel() {
    window.print();
}

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

    // Enable back button only if the checkbox is checked
    const confirmPrinted = document.getElementById('confirmPrinted');
    const backButton = document.getElementById('backButton');

    confirmPrinted.addEventListener('change', function() {
        if (confirmPrinted.checked) {
            backButton.classList.remove('disabled');
            backButton.addEventListener('click', backButtonClickHandler);
        } else {
            backButton.classList.add('disabled');
            backButton.removeEventListener('click', backButtonClickHandler);
        }
    });

    // Initial state of backButton
    if (!confirmPrinted.checked) {
        backButton.classList.add('disabled');
    } else {
        backButton.addEventListener('click', backButtonClickHandler);
    }

    function backButtonClickHandler(event) {
        if (backButton.classList.contains('disabled')) {
            event.preventDefault();
        }
    }
});
