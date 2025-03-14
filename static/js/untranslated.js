// untranslated.js
let untranslatedState = [];
let currentPage = 1, rowsPerPage = 10, totalPages = 1;

function loadUntranslated() {
    fetch("/translations/untranslated/all")
        .then(response => response.json())
        .then(data => {
            untranslatedState = data;
            updatePagination();
            updateTable();
        })
        .catch(error => console.error("Error loading untranslated entries:", error));
}

function updateRowsPerPage() {
    rowsPerPage = parseInt(this.value);
    currentPage = 1;
    updatePagination();
    updateTable();
}

function updatePagination() {
    totalPages = Math.ceil(untranslatedState.length / rowsPerPage);
    const paginationTop = document.getElementById("pagination-top");
    const paginationBottom = document.getElementById("pagination-bottom");
    paginationTop.innerHTML = "";
    paginationBottom.innerHTML = "";
    if (totalPages <= 1) return;
    let paginationHTML = "";

    for (let i = 1; i <= totalPages; i++) {
        paginationHTML += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
        </li>`;
    }
    paginationTop.innerHTML = paginationHTML;
    paginationBottom.innerHTML = paginationHTML;
}


function changePage(page) {
    currentPage = page;
    updatePagination();
    updateTable();
}

function updateTable() {
    const tbody = document.getElementById("untranslated-body");
    tbody.innerHTML = "";
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    untranslatedState.slice(start, end).forEach(item => {
        const row = document.createElement("tr");
        row.setAttribute("data-id", item._id);

        const englishCell = document.createElement("td");
        const englishDiv = document.createElement("div");
        englishDiv.classList.add("text-break", "overflow-auto");
        englishDiv.style.maxHeight = "120px";
        englishDiv.textContent = item.english || "—";
        englishCell.appendChild(englishDiv);

        const kurdishCell = document.createElement("td");
        const kurdishDiv = document.createElement("div");
        kurdishDiv.classList.add("text-break", "overflow-auto");
        kurdishDiv.style.maxHeight = "120px";
        kurdishDiv.textContent = item.kurdish || "—";
        kurdishCell.appendChild(kurdishDiv);

        const actionsCell = document.createElement("td");
        actionsCell.classList.add("text-center");

        const editButton = document.createElement("button");
        editButton.classList.add("btn", "btn-sm", "btn-outline-warning", "edit-btn", "mx-1");
        editButton.setAttribute("data-id", item._id);
        editButton.setAttribute("data-english", item.english || "");
        editButton.setAttribute("data-kurdish", item.kurdish || "");
        editButton.setAttribute("data-bs-toggle", "modal");
        editButton.setAttribute("data-bs-target", "#editModal");
        editButton.textContent = "✎";

        const deleteButton = document.createElement("button");
        deleteButton.classList.add("btn", "btn-sm", "btn-outline-danger", "delete-btn", "mx-1");
        deleteButton.setAttribute("data-id", item._id);
        deleteButton.textContent = "🗑";

        actionsCell.appendChild(editButton);
        actionsCell.appendChild(deleteButton);

        row.appendChild(englishCell);
        row.appendChild(kurdishCell);
        row.appendChild(actionsCell);

        tbody.appendChild(row);
    });

    bindEditButtons();
    bindDeleteButtons();
}

function bindEditButtons() {
    document.querySelectorAll(".edit-btn").forEach(button => {
        button.onclick = function () {
            document.getElementById("edit-id").value = button.getAttribute("data-id");
            document.getElementById("edit-english").value = button.getAttribute("data-english") || "";
            document.getElementById("edit-kurdish").value = button.getAttribute("data-kurdish") || "";
        };
    });
}

function bindDeleteButtons() {
    document.querySelectorAll(".delete-btn").forEach(button => {
        button.onclick = function () {
            let id = button.getAttribute("data-id");

            fetch("/translations/untranslated/delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: String(id) })
            }).then(response => response.json())
                .then(data => {
                    if (data.success) {
                        untranslatedState = untranslatedState.filter(item => item._id !== id);
                        updatePagination();
                        updateTable();
                    } else {
                        console.error("Delete failed:", data.error);
                    }
                })
                .catch(error => console.error("Error deleting untranslated entry:", error));
        };
    });
}

document.getElementById("save-edit").addEventListener("click", function () {
    let id = document.getElementById("edit-id").value;
    let english = document.getElementById("edit-english").value;
    let kurdish = document.getElementById("edit-kurdish").value;

    fetch("/translations/untranslated/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, english, kurdish })
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              loadUntranslated();
          } else {
              console.error("Update failed:", data.error);
          }
      })
      .catch(error => console.error("Error updating entry:", error))
      .finally(() => bootstrap.Modal.getInstance(document.getElementById('editModal')).hide());
})

document.getElementById("search-input").addEventListener("input", function () {
    let query = this.value.trim().toLowerCase();

    if (query.length === 0) {
        loadUntranslated();
        return;
    }

    fetch(`/translations/untranslated/search?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            untranslatedState = data;
            updatePagination();
            updateTable();
        })
        .catch(error => console.error("Error fetching search results:", error));
});

document.getElementById("refresh-container").addEventListener("click", function () {
    fetch("/translations/untranslated/refresh", { method: "POST" })
        .then(() => loadUntranslated())
        .catch(error => console.error("Error during refresh:", error));
});

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("rows-per-page").addEventListener("change", updateRowsPerPage);
    loadUntranslated();
});