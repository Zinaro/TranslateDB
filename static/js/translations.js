
let translationsState = [];
let currentPage = 1, rowsPerPage = 10, totalPages = 1;
function loadTranslations() {
    fetch("/translations/all")
        .then(response => response.json())
        .then(data => {
            translationsState = data;
            updatePagination();
            updateTable();
        })
        .catch(error => console.error("Error loading translations:", error));
}
function updateRowsPerPage() {
    rowsPerPage = parseInt(this.value);
    currentPage = 1;
    updatePagination();
    updateTable();
}

function updatePagination() {
    totalPages = Math.ceil(translationsState.length / rowsPerPage);
    let pagination = document.getElementById("pagination");
    pagination.innerHTML = "";
    if (totalPages <= 1) return;
    let paginationHTML = "";
    if (currentPage !== 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1)">1</a></li>`;
    }
    if (currentPage > 3) {
        paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    }
    for (let i = Math.max(2, currentPage - 2); i <= Math.min(totalPages - 1, currentPage + 2); i++) {
        paginationHTML += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
        </li>`;
    }
    if (currentPage < totalPages - 2) {
        paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    }
    if (currentPage !== totalPages) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages})">${totalPages}</a></li>`;
    }

    pagination.innerHTML = paginationHTML;
}

function changePage(page) {
    currentPage = page;
    updatePagination();
    updateTable();
}

function updateTable() {
    let tbody = document.getElementById("translations-body");
    tbody.innerHTML = "";
    let start = (currentPage - 1) * rowsPerPage, end = start + rowsPerPage;

    translationsState.slice(start, end).forEach(item => {
        tbody.innerHTML += `<tr data-id="${item._id}">
            <td>${item.english}</td>
            <td>${item.kurdish}</td>
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
            document.getElementById("edit-kurdish").value = button.getAttribute("data-kurdish");
        };
    });
}

function bindDeleteButtons() {
    document.querySelectorAll(".delete-btn").forEach(button => {
        button.onclick = function () {
            let id = button.getAttribute("data-id");

            fetch("/translations/delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: String(id) })
            }).then(response => response.json())
                .then(data => {
                    if (data.success) {
                        translationsState = translationsState.filter(item => item._id !== id);
                        updatePagination(); 
                        updateTable();
                    } else {
                        console.error("Delete failed:", data.error);
                    }
                })
                .catch(error => console.error("Error deleting translation:", error));
        };
    });
}


document.getElementById("save-edit").addEventListener("click", function () {
    let id = document.getElementById("edit-id").value;
    let english = document.getElementById("edit-english").value;
    let kurdish = document.getElementById("edit-kurdish").value;

    fetch("/translations/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: String(id), english, kurdish })
    }).then(response => response.json())
        .then(data => {
            if (data.success) {
                translationsState = translationsState.map(item =>
                    item._id === id ? { ...item, english, kurdish } : item
                );

                updateTable();

                let modal = document.getElementById("editModal");
                let modalInstance = bootstrap.Modal.getInstance(modal);
                modalInstance.hide();
            } else {
                console.error("Update failed:", data.error);
            }
        })
        .catch(error => console.error("Error updating translation:", error));
});
document.getElementById("search-input").addEventListener("input", function () {
    let query = this.value.trim().toLowerCase();

    if (query.length === 0) {
        loadTranslations();
        return;
    }

    fetch(`/translations/search?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            translationsState = data;
            updateTable();
        })
        .catch(error => console.error("Error fetching search results:", error));
});
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("editModal").addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            event.preventDefault(); 
            document.getElementById("save-edit").click();
        }
    });
});
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("rows-per-page").addEventListener("change", updateRowsPerPage);
    loadTranslations();
});


document.addEventListener("DOMContentLoaded", loadTranslations);


