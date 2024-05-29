document.addEventListener("DOMContentLoaded", function() {
    // Define the required fields for the form.
    const requiredFields = [
        'machine', 'operation', 'shift', 'operator', 'tool_type', 'tool_status', 'tool_issue', 'expected_tool_life', 'actual_tool_life'
    ];

    // Get the submit button element.
    const submitButton = document.querySelector(".submit-button");

    // Check if the submit button exists.
    if (!submitButton) {
        console.error("Submit button not found");
    }

    // Get the tool issue and comments input elements.
    const toolIssueInput = document.querySelector('[name="tool_issue"]');
    const commentsInput = document.querySelector('[name="comments"]');

    // Get the container of the comments input field to append the notification message.
    const commentsContainer = commentsInput.closest('div');

    if (commentsContainer) {
        // Create a notification message element.
        const notification = document.createElement('div');
        notification.className = 'text-danger mt-2';
        notification.style.display = 'none';
        notification.textContent = 'Please specify the issue in the comments when selecting "Other".';
        commentsContainer.appendChild(notification);

        /**
         * checkFields
         * 
         * Checks if all required fields are filled.
         * 
         * @returns {boolean} - True if all required fields are filled, false otherwise.
         */
        function checkFields() {
            let allFilled = true;

            // Iterate over each required field and check if it is filled.
            requiredFields.forEach(field => {
                const input = document.querySelector(`[name="${field}"]`);
                if (!input) {
                    console.error(`Input field with name '${field}' not found`);
                } else if (input.value.trim() === "") {
                    allFilled = false;
                }
            });

            // Check if the tool issue is "Other" and comments are empty.
            if (toolIssueInput && commentsInput && toolIssueInput.value === "Other") {
                if (commentsInput.value.trim() === "") {
                    allFilled = false;
                    notification.style.display = 'block'; // Show notification
                } else {
                    notification.style.display = 'none'; // Hide notification
                }
            } else {
                notification.style.display = 'none'; // Hide notification
            }

            return allFilled;
        }

        /**
         * toggleSubmitButton
         * 
         * Enables or disables the submit button based on whether all required fields are filled.
         */
        function toggleSubmitButton() {
            if (checkFields()) {
                submitButton.disabled = false;
            } else {
                submitButton.disabled = true;
            }
        }

        // Add input event listeners to all required fields to toggle the submit button.
        requiredFields.forEach(field => {
            const input = document.querySelector(`[name="${field}"]`);
            if (input) {
                input.addEventListener("input", function() {
                    toggleSubmitButton();
                });
            } else {
                console.error(`Input field with name '${field}' not found during event listener assignment`);
            }
        });

        // Add input event listener to the comments field to toggle the submit button.
        if (commentsInput) {
            commentsInput.addEventListener("input", function() {
                toggleSubmitButton();
            });
        }

        // Add change event listener to the tool issue field to toggle the submit button.
        if (toolIssueInput) {
            toolIssueInput.addEventListener("change", function() {
                toggleSubmitButton();
            });
        }

        // Initial call to set the submit button state on page load.
        toggleSubmitButton();

        // Get the tool status, tool issue, actual tool life, and expected tool life input elements.
        const toolStatusInput = document.querySelector('[name="tool_status"]');
        const actualToolLifeInput = document.querySelector('[name="actual_tool_life"]');
        const expectedToolLifeInput = document.querySelector('[name="expected_tool_life"]');

        // Add change event listener to tool status input to update related fields.
        if (toolStatusInput && toolIssueInput && actualToolLifeInput && expectedToolLifeInput) {
            toolStatusInput.addEventListener("change", function() {
                if (toolStatusInput.value === "Tool Life Achieved") {
                    toolIssueInput.value = "No issue";
                    actualToolLifeInput.value = expectedToolLifeInput.value;
                    toggleSubmitButton(); // Ensure the button state is updated after the fields are modified
                }
            });
        }

        // Get the form element.
        const form = document.getElementById("toolReportForm");
        
        // Add submit event listener to the form to parse numerical inputs and prevent submission if comments are empty when "Other" is selected.
        if (form) {
            form.addEventListener("submit", function(event) {
                const machineInput = document.querySelector('[name="machine"]');
                const operationInput = document.querySelector('[name="operation"]');

                if (machineInput && operationInput) {
                    machineInput.value = parseInt(machineInput.value, 10);
                    operationInput.value = parseInt(operationInput.value, 10);
                }

                if (toolIssueInput && toolIssueInput.value === "Other" && commentsInput.value.trim() === "") {
                    event.preventDefault();
                }
            });
        }
    }
});
