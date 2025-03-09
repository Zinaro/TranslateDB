let translationsState = [];
let currentPage = 1, rowsPerPage = 10, totalPages = 1;
document.getElementById("allAcceptBtn").addEventListener("click", function () {
    translationsState.forEach(translation => translation.approved = true);
    updatePagination();
    updateTable();
});
document.getElementById("removeSelectedBtn").addEventListener("click", function () {
    const rows = document.querySelectorAll("#translations-body tr");
    rows.forEach((row, index) => {
        if (translationsState[index].approved) {
            translationsState[index].approved = false;
            row.classList.remove("table-success");
            row.classList.remove("table-danger");
        }
    });
});

function updateTable() {
    const tbody = document.getElementById("translations-body");
    tbody.innerHTML = "";

    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const paginatedItems = translationsState.slice(start, end);

    paginatedItems.forEach((translation, index) => {
        const globalIndex = start + index;
        const row = document.createElement("tr");
        row.classList.toggle("table-success", translation.approved);
        row.setAttribute("data-index", globalIndex);
        row.innerHTML = `
    <td class="align-middle">${translation.msgid}</td>
    <td class="align-middle">
        <textarea class="form-control translation-input" data-index="${index}" rows="1">${translation.msgstr}</textarea>
    </td>
    <td class="text-center align-middle">
        <div class="d-grid gap-2 d-md-flex justify-content-md-center">
            <button class="btn btn-sm btn-success approve-btn">✔</button>
            <button class="btn btn-sm btn-danger reject-btn">✖</button>
        </div>
    </td>
`;
        tbody.appendChild(row);
    });


    setupRowActions();
    document.getElementById("exportBtn").style.display = "block";
}

function updatePagination() {
    totalPages = Math.ceil(translationsState.length / rowsPerPage);
    const paginationTop = document.getElementById("pagination-top");

    paginationTop.innerHTML = "";
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
}

function changePage(page) {
    currentPage = page;
    updatePagination();
    updateTable();
}

document.getElementById("rows-per-page").addEventListener("change", function () {
    rowsPerPage = parseInt(this.value);
    currentPage = 1;
    updatePagination();
    updateTable();
});

document.getElementById("uploadBtn").addEventListener("click", function () {
    const fileInput = document.getElementById("fileInput");
    const uploadStatus = document.getElementById("uploadStatus");
    const translationsContainer = document.getElementById("translations-container");
    uploadStatus.innerHTML = "";
    translationsContainer.style.display = "none";

    if (fileInput.files.length === 0) {
        showMessage("Please select a file!", "danger");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    fetch("/work/upload", {
        method: "POST",
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            console.log("Server Response:", data);
            showMessage(data.message, "success");

            if (data.translations.length > 0) {
                translationsContainer.style.display = "block";
                loadTranslations(data.translations);
                document.getElementById("uploadForm").reset();
            }
        })
        .catch(error => {
            console.error("Fetch Error:", error);
            showMessage("Error: " + error.message, "danger");
        });
});

function showMessage(message, type) {
    document.getElementById("uploadStatus").innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>`;
        setTimeout(() => {
            const alert = uploadStatus.querySelector('.alert');
            if (alert) {
                alert.classList.remove('show');
                alert.classList.add('fade');
                setTimeout(() => alert.remove(), 300);
            }
        }, 3000);
}

function loadTranslations(translations) {
    translationsState = translations.map(t => ({
        msgid: t.msgid,
        msgstr: t.msgstr,
        approved: t.approved || false
    }));

    updatePagination();
    updateTable();
}



function setupRowActions() {
    document.querySelectorAll(".approve-btn").forEach(button => {
        button.addEventListener("click", function () {
            const row = this.closest("tr");
            row.classList.add("table-success");
            row.classList.remove("table-danger");

            const index = parseInt(row.getAttribute("data-index"));
            translationsState[index].approved = true;
        });
    });

    document.querySelectorAll(".reject-btn").forEach(button => {
        button.addEventListener("click", function () {
            const row = this.closest("tr");
            row.classList.add("table-danger");
            row.classList.remove("table-success");

            const index = parseInt(row.getAttribute("data-index"));
            translationsState[index].approved = false;
        });
    });
}


document.getElementById("exportBtn").addEventListener("click", exportTranslations);

function exportTranslations() {
    const rows = document.querySelectorAll("#translations-body tr");
    const updatedTranslations = [];

    rows.forEach(row => {
        const msgid = row.children[0].textContent.trim();
        const msgstr = row.children[1].querySelector("textarea").value.trim();
        const approved = row.classList.contains("table-success");

        updatedTranslations.push({ msgid, msgstr, approved });
    });

    fetch("/work/save_and_export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ translations: updatedTranslations })
    })
        .then(response => response.json())
        .then(data => {
            if (data.download_url) {
                console.log("Downloading file:", data.download_url);
                window.location.href = data.download_url;
            } else {
                alert("Error: " + (data.error || "Could not export file."));
            }
        })
        .catch(error => {
            alert("Error exporting file: " + error.message);
        });
}