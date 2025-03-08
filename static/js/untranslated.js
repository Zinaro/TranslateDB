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
    let tbody = document.getElementById("untranslated-body");
    tbody.innerHTML = "";
    let start = (currentPage - 1) * rowsPerPage, end = start + rowsPerPage;

    untranslatedState.slice(start, end).forEach(item => {
        tbody.innerHTML += `<tr data-id="${item._id}">
            <td>${item.english}</td>
            <td>${item.kurdish || "—"}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-warning edit-btn"
                    data-id="${item._id}" 
                    data-english="${item.english}" 
                    data-kurdish="${item.kurdish}"
                    data-bs-toggle="modal"
                    data-bs-target="#editModal">
                    ✎
                </button>
                <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${item._id}">🗑</button>
            </td>
        </tr>`;
    });

    bindEditButtons();
    bindDeleteButtons();
}

function bindEditButtons() {
    document.querySelectorAll(".edit-btn").forEach(button => {
        button.onclick = function () {
            document.getElementById("edit-id").value = button.getAttribute("data-id");
            document.getElementById("edit-english").value = button.getAttribute("data-english");
            document.getElementById("edit-kurdish").value = button.getAttribute("data-kurdish") || '';
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
                body: JSON.stringify({ id: id })
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