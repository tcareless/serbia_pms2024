document.addEventListener("DOMContentLoaded", function() {
    const editButtons = document.querySelectorAll(".edit-button");

    editButtons.forEach(button => {
        button.addEventListener("click", function() {
            const entryId = this.getAttribute("data-id");
            fetch(`/tooling/edit/${entryId}/`)
                .then(response => response.text())
                .then(html => {
                    document.querySelector("#editModal .modal-body").innerHTML = html;
                    document.getElementById("editForm").action = `/tooling/edit/${entryId}/`;
                    $("#editModal").modal("show");
                });
        });
    });

    const editForm = document.getElementById("editForm");
    editForm.addEventListener("submit", function(event) {
        event.preventDefault();
        const formData = new FormData(editForm);
        fetch(editForm.action, {
            method: "POST",
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                $("#editModal").modal("hide");
                location.reload();
            } else {
                alert("Failed to update entry.");
            }
        });
    });

    // Add event listeners for the modal close buttons
    document.querySelectorAll('[data-dismiss="modal"]').forEach(button => {
        button.addEventListener("click", function() {
            $("#editModal").modal("hide");
        });
    });

    // Optional: Ensure modal is reset when hidden
    $('#editModal').on('hidden.bs.modal', function () {
        document.querySelector("#editModal .modal-body").innerHTML = '';
    });
});
