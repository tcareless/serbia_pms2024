/**
 * toolLife.js
 *
 * This script handles the dynamic updating of the expected tool life based on the selected tool type.
 * It maps specific tool types to their respective expected tool life values and updates the form accordingly.
 * The script is executed when the DOM content is fully loaded.
 *
 * Functionality:
 * 1. Update the expected tool life input field based on the selected tool type.
 *
 * Tool Life Mapping:
 * - Drill: 750
 * - Reamer: 250
 *
 * Dependencies:
 * - Assumes the tool type input field has the name 'tool_type'.
 * - Assumes the expected tool life input field has the name 'expected_tool_life'.
 */

document.addEventListener("DOMContentLoaded", function() {
    // Define the mapping of tool types to their respective expected tool life values.
    const toolLifeMapping = {
        'Drill': 750,
        'Reamer': 250
    };

    // Get the tool type and expected tool life input elements.
    const toolTypeInput = document.querySelector('[name="tool_type"]');
    const expectedToolLifeInput = document.querySelector('[name="expected_tool_life"]');

    // Add change event listener to the tool type input to update the expected tool life.
    toolTypeInput.addEventListener("change", function() {
        // Get the selected tool type value.
        const selectedToolType = toolTypeInput.value;

        // Check if the selected tool type is in the tool life mapping.
        if (toolLifeMapping[selectedToolType] !== undefined) {
            // Set the expected tool life input value to the corresponding value from the mapping.
            expectedToolLifeInput.value = toolLifeMapping[selectedToolType];
        } else {
            // Clear the expected tool life input value if the tool type is not in the mapping.
            expectedToolLifeInput.value = '';
        }
    });
});
