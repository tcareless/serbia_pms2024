// Event listener to execute the function when the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("toolReportForm");
    const submitButton = document.querySelector(".submit-button");
    // List of required field names
    const requiredFields = [
        'machine', 'operation', 'shift', 'operator', 'tool_type', 'tool_status', 'tool_issue', 'expected_tool_life', 'actual_tool_life', 'tool_serial_number'
    ];

    // check if all required fields are filled
    function checkFields() {
        let allFilled = true; // Flag to track if all fields are filled
        requiredFields.forEach(field => {
            // Get the input element by its name attribute
            const input = document.querySelector(`[name="${field}"]`);
            // Check if the input value is empty or whitespace
            if (input.value.trim() === "") {
                allFilled = false; // Set flag to false if any field is empty
            }
        });
        return allFilled; // Return the flag indicating if all fields are filled
    }

    // Function to enable or disable the submit button based on field validation
    function toggleSubmitButton() {
        if (checkFields()) {
            submitButton.disabled = false; // Enable submit button if all fields are filled
        } else {
            submitButton.disabled = true; // Disable submit button if any field is empty
        }
    }

    // Add event listener to each required field to check input and toggle submit button
    requiredFields.forEach(field => {
        const input = document.querySelector(`[name="${field}"]`);
        input.addEventListener("input", toggleSubmitButton); // Check fields on input change
    });

    // Event listener to handle form submission
    form.addEventListener("submit", function(event) {
        event.preventDefault(); // Prevent default form submission

        // Get specific input elements and parse their values to integers
        const machineInput = document.querySelector('[name="machine"]');
        const operationInput = document.querySelector('[name="operation"]');

        machineInput.value = parseInt(machineInput.value, 10); // Parse machine input to integer
        operationInput.value = parseInt(operationInput.value, 10); // Parse operation input to integer

        form.submit(); // Submit the form programmatically
    });

    toggleSubmitButton(); // Initial call to set the submit button state on page load
});
