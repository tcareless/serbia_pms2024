document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("toolReportForm");
    const submitButton = document.querySelector(".submit-button");
    const requiredFields = [
        'machine', 'operation', 'shift', 'operator', 'tool_type', 'tool_status', 'tool_issue', 'expected_tool_life', 'actual_tool_life', 'tool_serial_number'
    ];

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

    function toggleSubmitButton() {
        if (checkFields()) {
            submitButton.disabled = false;
        } else {
            submitButton.disabled = true;
        }
    }

    requiredFields.forEach(field => {
        const input = document.querySelector(`[name="${field}"]`);
        input.addEventListener("input", toggleSubmitButton);
    });

    form.addEventListener("submit", function(event) {
        event.preventDefault();

        const machineInput = document.querySelector('[name="machine"]');
        const operationInput = document.querySelector('[name="operation"]');

        machineInput.value = parseInt(machineInput.value, 10);
        operationInput.value = parseInt(operationInput.value, 10);

        form.submit();
    });

    toggleSubmitButton();
});
