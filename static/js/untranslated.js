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

    untranslatedState.slice(start, end).forEach((item, index) => {
        const globalIndex = start + index;
        const row = document.createElement("tr");
        row.setAttribute("data-id", item._id);

        const englishCell = document.createElement("td");
        englishCell.classList.add("align-middle");
        const englishDiv = document.createElement("div");
        englishDiv.classList.add("text-break", "overflow-auto");
        englishDiv.style.maxHeight = "200px";
        englishDiv.textContent = item.english || "";
        englishCell.appendChild(englishDiv);

        const kurdishCell = document.createElement("td");
        kurdishCell.classList.add("align-middle");
        const textarea = document.createElement("textarea");
        textarea.classList.add("form-control", "translation-input", "overflow-auto", "text-break");
        textarea.setAttribute("data-index", globalIndex);
        textarea.setAttribute("rows", "1");
        textarea.style.maxHeight = "200px";
        textarea.textContent = item.kurdish || item.googletrans || "";
        kurdishCell.appendChild(textarea);

        const actionsCell = document.createElement("td");
        actionsCell.classList.add("text-center", "align-middle");

        actionsCell.innerHTML = `
            <div class="d-grid gap-2 d-md-flex justify-content-md-center">
                <button class="btn btn-sm btn-warning google-translate-btn">🌐</button>
                <button class="btn btn-sm btn-success approve-btn">✔</button>
                <button class="btn btn-sm btn-danger reject-btn">✖</button>
            </div>
        `;

        row.appendChild(englishCell);
        row.appendChild(kurdishCell);
        row.appendChild(actionsCell);

        tbody.appendChild(row);
    });

    setTimeout(setupRowActions, 0);
}

function setupRowActions() {
    document.querySelectorAll(".approve-btn").forEach(button => {
        button.onclick = function () {
            const row = button.closest("tr");
            const id = row.getAttribute("data-id");
            const english = row.querySelector("td:first-child div").textContent.trim();
            const kurdish = row.querySelector(".translation-input").value.trim();

            if (kurdish === "") {
                console.log("Kurdish text is empty, not sending to backend.");
                return;
            }

            fetch("/translations/untranslated/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id, english, kurdish })
            }).then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log("Update successful, reloading data...");
                        loadUntranslated();
                    } else {
                        console.error("Update failed:", data.error);
                    }
                })
                .catch(error => console.error("Error updating entry:", error));
        };
    });

    document.querySelectorAll(".reject-btn").forEach(button => {
        button.onclick = function () {
            const row = button.closest("tr");
            const id = row.getAttribute("data-id");

            fetch("/translations/untranslated/delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id })
            }).then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log("Delete successful, removing row...");
                        untranslatedState = untranslatedState.filter(item => String(item._id) !== id);
                        updateTable();
                        updatePagination();
                    } else {
                        console.error("Delete failed:", data.error);
                    }
                })
                .catch(error => console.error("Error deleting untranslated entry:", error));
        };
    });

    document.querySelectorAll(".google-translate-btn").forEach(button => {
        button.onclick = function () {
            const row = button.closest("tr");
            const id = row.getAttribute("data-id");
            const english = row.querySelector("td:first-child div").textContent.trim();
            fetch("/translations/untranslated/google_translate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id, english })
            }).then(response => response.json())
                .then(data => {
                    if (data.success) {
                        row.querySelector(".translation-input").value = data.googletrans;
                        const item = untranslatedState.find(item => item._id === id);
                        if (item) {
                            item.googletrans = data.googletrans;
                        }
                    } else {
                        console.error("Translation failed:", data.error);
                    }
                });
        };
    });

}




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

document.getElementById("translate-visible-btn").addEventListener("click", function () {
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const visibleEntries = untranslatedState.slice(start, end);

    visibleEntries.forEach(item => {
        if (!item.googletrans && !item.kurdish) {
            fetch("/translations/untranslated/google_translate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: item._id, english: item.english })
            }).then(response => response.json())
                .then(data => {
                    if (data.success) {
                        item.googletrans = data.googletrans;
                        updateTable();
                    } else {
                        console.error("Translation failed for:", item.english);
                    }
                })
                .catch(error => console.error("Translation error:", error));
        }
    });
});

