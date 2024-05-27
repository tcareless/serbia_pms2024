/**
 * fieldValidation.js
 *
 * This script handles the form validation and dynamic behavior for the tool report form.
 * It ensures that required fields are filled before enabling the submit button and updates
 * fields based on the selection of the tool status. The script is executed when the DOM
 * content is fully loaded.
 *
 * Functionality:
 * 1. Disable the submit button until all required fields are filled.
 * 2. Automatically set the tool issue and actual tool life when the tool status is "Tool Life Achieved".
 * 3. Parse numerical input values to integers before form submission.
 *
 * Required Fields:
 * - machine
 * - operation
 * - shift
 * - operator
 * - tool_type
 * - tool_status
 * - tool_issue
 * - expected_tool_life
 * - actual_tool_life
 *
 */

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

    // Initial call to set the submit button state on page load.
    toggleSubmitButton();

    // Get the tool status, tool issue, actual tool life, and expected tool life input elements.
    const toolStatusInput = document.querySelector('[name="tool_status"]');
    const toolIssueInput = document.querySelector('[name="tool_issue"]');
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
    
    // Add submit event listener to the form to parse numerical inputs.
    if (form) {
        form.addEventListener("submit", function() {
            const machineInput = document.querySelector('[name="machine"]');
            const operationInput = document.querySelector('[name="operation"]');

            if (machineInput && operationInput) {
                machineInput.value = parseInt(machineInput.value, 10);
                operationInput.value = parseInt(operationInput.value, 10);
            }
        });
    }
});
