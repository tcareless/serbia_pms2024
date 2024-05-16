document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("toolReportForm");
    const submitButton = document.querySelector(".submit-button");

    // List of required field names, excluding 'comments'
    const requiredFields = [
        'machine', 'operation', 'shift', 'operator', 'tool_type', 'tool_status', 'tool_issue', 'expected_tool_life', 'actual_tool_life', 'tool_serial_number'
    ];

    // Tool type to expected tool life mapping
    const toolLifeMapping = {
        'Drill': 750,
        'Reamer': 250
    };

    // Function to check if all required fields are filled
    function checkFields() {
        let allFilled = true;
        requiredFields.forEach(field => {
            const input = document.querySelector(`[name="${field}"]`);
            if (input.value.trim() === "") {
                allFilled = false;
            }
        });
        return allFilled;
    }

    // Function to enable or disable the submit button based on field validation
    function toggleSubmitButton() {
        if (checkFields()) {
            submitButton.disabled = false;
        } else {
            submitButton.disabled = true;
        }
    }

    // Add event listener to each required field to check input and toggle submit button
    requiredFields.forEach(field => {
        const input = document.querySelector(`[name="${field}"]`);
        input.addEventListener("input", toggleSubmitButton);
    });

    // Event listener to autofill the expected tool life based on tool type
    const toolTypeInput = document.querySelector('[name="tool_type"]');
    const expectedToolLifeInput = document.querySelector('[name="expected_tool_life"]');

    toolTypeInput.addEventListener("change", function() {
        const selectedToolType = toolTypeInput.value;
        if (toolLifeMapping[selectedToolType] !== undefined) {
            expectedToolLifeInput.value = toolLifeMapping[selectedToolType];
        } else {
            expectedToolLifeInput.value = '';
        }
    });

    // Event listener to handle form submission
    form.addEventListener("submit", function() {
        // Get specific input elements and parse their values to integers
        const machineInput = document.querySelector('[name="machine"]');
        const operationInput = document.querySelector('[name="operation"]');

        machineInput.value = parseInt(machineInput.value, 10);
        operationInput.value = parseInt(operationInput.value, 10);
    });

    toggleSubmitButton(); // Initial call to set the submit button state on page load
});
