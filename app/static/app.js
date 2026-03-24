const state = {
    selectedFiles: [],
    user: null,
};

const authPanel = document.querySelector("#auth-panel");
const appPanel = document.querySelector("#app-panel");
const toast = document.querySelector("#toast");
const loginForm = document.querySelector("#login-form");
const registerForm = document.querySelector("#register-form");
const showLoginButton = document.querySelector("#show-login");
const showRegisterButton = document.querySelector("#show-register");
const welcomeCopy = document.querySelector("#welcome-copy");
const selectedFilesContainer = document.querySelector("#selected-files");
const fileInput = document.querySelector("#file-input");
const browseButton = document.querySelector("#browse-button");
const uploadButton = document.querySelector("#upload-button");
const dropzone = document.querySelector("#dropzone");
const logoutButton = document.querySelector("#logout-button");
const uploadsList = document.querySelector("#uploads-list");
const transactionsBody = document.querySelector("#transactions-body");

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.remove("hidden");
    toast.style.background = isError ? "#8a1c13" : "#1f2d3a";
    window.clearTimeout(showToast.timeoutId);
    showToast.timeoutId = window.setTimeout(() => toast.classList.add("hidden"), 3200);
}

async function api(path, options = {}) {
    const response = await fetch(path, {
        credentials: "same-origin",
        headers: {
            ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
            ...(options.headers || {}),
        },
        ...options,
    });

    const payload = response.headers.get("content-type")?.includes("application/json")
        ? await response.json()
        : null;

    if (!response.ok) {
        throw new Error(payload?.detail || "Request failed.");
    }

    return payload;
}

function switchAuthMode(mode) {
    const showLogin = mode === "login";
    loginForm.classList.toggle("hidden", !showLogin);
    registerForm.classList.toggle("hidden", showLogin);
    showLoginButton.classList.toggle("active", showLogin);
    showRegisterButton.classList.toggle("active", !showLogin);
}

function formatCurrency(value) {
    const numericValue = Number(value || 0);
    return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
    }).format(numericValue);
}

function formatDate(value) {
    if (!value) {
        return "-";
    }
    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    }).format(new Date(value));
}

function setSelectedFiles(files) {
    state.selectedFiles = [...files];
    selectedFilesContainer.innerHTML = state.selectedFiles.length
        ? state.selectedFiles.map((file) => `<div class="file-chip">${file.name}</div>`).join("")
        : '<p class="empty-state">No files selected yet.</p>';
}

function renderUploads(uploads) {
    if (!uploads?.length) {
        uploadsList.innerHTML = '<p class="empty-state">Your uploads will appear here after processing.</p>';
        return;
    }

    uploadsList.innerHTML = uploads.map((upload) => `
        <article class="upload-item">
            <div>
                <strong>${upload.original_filename}</strong>
                <p class="upload-meta">${upload.transaction_count} transaction(s)</p>
            </div>
            <div class="upload-status">
                <span class="status-pill ${upload.status}">${upload.status}</span>
                <p>${formatDate(upload.created_at)}</p>
            </div>
        </article>
    `).join("");
}

function renderTransactions(transactions) {
    if (!transactions?.length) {
        transactionsBody.innerHTML = '<tr><td colspan="5" class="empty-state">No transactions loaded yet.</td></tr>';
        return;
    }

    transactionsBody.innerHTML = transactions.map((transaction) => `
        <tr>
            <td>${formatDate(transaction.transaction_date)}</td>
            <td>${transaction.description || "-"}</td>
            <td><span class="${transaction.transaction_type === "CREDIT" ? "credit" : "debit"}">${transaction.transaction_type || "-"}</span></td>
            <td>${formatCurrency(transaction.amount)}</td>
            <td>${formatCurrency(transaction.balance)}</td>
        </tr>
    `).join("");
}

function renderSummary(summary) {
    document.querySelector("#stat-transactions").textContent = summary.transaction_count ?? 0;
    document.querySelector("#stat-credits").textContent = formatCurrency(summary.total_credits);
    document.querySelector("#stat-debits").textContent = formatCurrency(summary.total_debits);
    document.querySelector("#stat-balance").textContent = formatCurrency(summary.latest_balance);
}

function setAuthenticated(user) {
    state.user = user;
    authPanel.classList.add("hidden");
    appPanel.classList.remove("hidden");
    welcomeCopy.textContent = `Welcome, ${user.email}`;
}

function clearAuthenticatedState() {
    state.user = null;
    authPanel.classList.remove("hidden");
    appPanel.classList.add("hidden");
    setSelectedFiles([]);
    switchAuthMode("login");
}

async function loadDashboard() {
    const payload = await api("/api/dashboard");
    renderSummary(payload.summary);
    renderUploads(payload.uploads);
    renderTransactions(payload.transactions);
}

async function submitAuthForm(event, path) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = Object.fromEntries(formData.entries());

    try {
        const data = await api(path, {
            method: "POST",
            body: JSON.stringify(payload),
        });
        setAuthenticated(data.user);
        await loadDashboard();
        showToast(path.includes("register") ? "Account created." : "Logged in.");
        event.currentTarget.reset();
    } catch (error) {
        showToast(error.message, true);
    }
}

async function uploadFiles() {
    if (!state.selectedFiles.length) {
        showToast("Choose at least one PDF first.", true);
        return;
    }

    const formData = new FormData();
    state.selectedFiles.forEach((file) => formData.append("files", file));

    uploadButton.disabled = true;
    uploadButton.textContent = "Processing...";

    try {
        const payload = await api("/api/uploads", {
            method: "POST",
            body: formData,
        });
        renderSummary(payload.summary);
        renderUploads(payload.uploads);
        renderTransactions(payload.transactions);
        setSelectedFiles([]);
        showToast(payload.results.map((result) => `${result.original_filename}: ${result.message}`).join(" "));
    } catch (error) {
        showToast(error.message, true);
    } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = "Upload and process";
        fileInput.value = "";
    }
}

async function bootstrap() {
    switchAuthMode("login");
    setSelectedFiles([]);

    try {
        const payload = await api("/api/auth/me");
        setAuthenticated(payload.user);
        await loadDashboard();
    } catch (_) {
        clearAuthenticatedState();
    }
}

showLoginButton.addEventListener("click", () => switchAuthMode("login"));
showRegisterButton.addEventListener("click", () => switchAuthMode("register"));
loginForm.addEventListener("submit", (event) => submitAuthForm(event, "/api/auth/login"));
registerForm.addEventListener("submit", (event) => submitAuthForm(event, "/api/auth/register"));
browseButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (event) => setSelectedFiles(event.target.files));
uploadButton.addEventListener("click", uploadFiles);
logoutButton.addEventListener("click", async () => {
    try {
        await api("/api/auth/logout", { method: "POST" });
        clearAuthenticatedState();
        showToast("Logged out.");
    } catch (error) {
        showToast(error.message, true);
    }
});

["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add("dragover");
    });
});

["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.remove("dragover");
    });
});

dropzone.addEventListener("drop", (event) => {
    const files = [...event.dataTransfer.files].filter((file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"));
    setSelectedFiles(files);
});

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        fileInput.click();
    }
});

bootstrap();