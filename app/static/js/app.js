const grammarInput = document.getElementById("grammarInput");
const stringsInput = document.getElementById("stringsInput");
const validateBtn = document.getElementById("validateBtn");
const resultsContainer = document.getElementById("resultsContainer");
const statusMessage = document.getElementById("statusMessage");
const loadExampleBtn = document.getElementById("loadExampleBtn");
const examplesDrawer = document.getElementById("examplesDrawer");
const startSymbolSelect = document.getElementById("startSymbolSelect");
const grammarErrorHint = document.getElementById("grammarErrorHint");
const workTitleInput = document.getElementById("workTitleInput");
const historyToggleBtn = document.getElementById("historyToggleBtn");
const saveSnapshotBtn = document.getElementById("saveSnapshotBtn");
const historyDrawer = document.getElementById("historyDrawer");
const historyList = document.getElementById("historyList");
const cloudHistoryList = document.getElementById("cloudHistoryList");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
const derivationModeSelect = document.getElementById("derivationModeSelect");
const saveCloudBtn = document.getElementById("saveCloudBtn");
const authUsernameInput = document.getElementById("authUsernameInput");
const authPasswordInput = document.getElementById("authPasswordInput");
const loginBtn = document.getElementById("loginBtn");
const registerBtn = document.getElementById("registerBtn");
const logoutBtn = document.getElementById("logoutBtn");
const loadCloudHistoryBtn = document.getElementById("loadCloudHistoryBtn");
const authStateBadge = document.getElementById("authStateBadge");
const authWelcomeText = document.getElementById("authWelcomeText");
const authMessage = document.getElementById("authMessage");
const authGuestView = document.getElementById("authGuestView");
const authUserView = document.getElementById("authUserView");
const refreshLibraryBtn = document.getElementById("refreshLibraryBtn");
const cloudLibraryState = document.getElementById("cloudLibraryState");
const cloudLibraryList = document.getElementById("cloudLibraryList");

const examples = window.INITIAL_EXAMPLES || [];
let currentUser = window.INITIAL_USER || null;
const STORAGE_VERSION = "v2";
const AUTOSAVE_KEY = `bnf-validator-autosave-${STORAGE_VERSION}`;
const HISTORY_KEY = `bnf-validator-history-${STORAGE_VERSION}`;
const CLOUD_IMPORT_KEY = "bnf-validator-cloud-import";
const MAX_HISTORY_ITEMS = 12;

let autosaveTimer = null;

function init() {
    cleanupLegacyStorage();
    const restored = restoreAutosave();
    restoreCloudImport();

    if (!derivationModeSelect.value) {
        derivationModeSelect.value = "leftmost";
    }

    if (!restored && examples.length > 0) {
        applyExample(examples[0]);
    } else {
        updateStartSymbols([]);
        syncStartSymbolsFromGrammar();
    }

    loadExampleBtn.addEventListener("click", () => {
        const willOpen = examplesDrawer.classList.contains("hidden");
        examplesDrawer.classList.toggle("hidden");
        historyDrawer.classList.add("hidden");
        loadExampleBtn.textContent = willOpen ? "Ocultar ejemplos" : "Ver ejemplos";
        setStatus(
            willOpen
                ? "Selecciona un ejemplo de la lista para cargarlo en el editor."
                : "Lista de ejemplos oculta.",
            "neutral",
        );
        if (willOpen) {
            examplesDrawer.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
    });

    historyToggleBtn.addEventListener("click", () => {
        historyDrawer.classList.toggle("hidden");
        examplesDrawer.classList.add("hidden");
        renderHistory();
    });

    document.querySelectorAll(".example-card").forEach((button, index) => {
        button.addEventListener("click", () => {
            applyExample(examples[index]);
            examplesDrawer.classList.add("hidden");
            loadExampleBtn.textContent = "Ver ejemplos";
        });
    });

    grammarInput.addEventListener("input", handleEditorChange);
    stringsInput.addEventListener("input", scheduleAutosave);
    startSymbolSelect.addEventListener("change", scheduleAutosave);
    derivationModeSelect.addEventListener("change", scheduleAutosave);
    workTitleInput.addEventListener("input", scheduleAutosave);
    validateBtn.addEventListener("click", validateGrammar);
    saveSnapshotBtn.addEventListener("click", () => saveSnapshot(true));
    saveCloudBtn.addEventListener("click", saveCloudSnapshot);
    clearHistoryBtn.addEventListener("click", clearHistory);
    loginBtn?.addEventListener("click", () => submitAuth("login"));
    registerBtn?.addEventListener("click", () => submitAuth("register"));
    logoutBtn?.addEventListener("click", logoutUser);
    loadCloudHistoryBtn?.addEventListener("click", loadCloudHistory);
    refreshLibraryBtn?.addEventListener("click", loadCloudHistory);

    renderHistory();
    syncAuthUI();
    if (currentUser) {
        loadCloudHistory();
    } else {
        renderCloudHistory([]);
    }
}

function applyExample(example) {
    workTitleInput.value = example.name ? `Ejemplo: ${example.name}` : "";
    grammarInput.value = example.grammar;
    stringsInput.value = example.inputs;
    syncStartSymbolsFromGrammar();
    clearGrammarError();
    scheduleAutosave();
    setStatus("Ejemplo cargado. Puedes editarlo antes de validar.", "neutral");
    clearResults();
}

function handleEditorChange() {
    syncStartSymbolsFromGrammar();
    clearGrammarError();
    scheduleAutosave();
}

function syncStartSymbolsFromGrammar() {
    const symbols = [...grammarInput.value.matchAll(/<[^<>\s]+>/g)].map((match) => match[0]);
    const unique = [...new Set(symbols)];
    updateStartSymbols(unique);
}

function updateStartSymbols(symbols) {
    const previous = startSymbolSelect.value;
    startSymbolSelect.innerHTML = "";

    if (symbols.length === 0) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "Detectado automaticamente";
        startSymbolSelect.appendChild(option);
        return;
    }

    symbols.forEach((symbol, index) => {
        const option = document.createElement("option");
        option.value = symbol;
        option.textContent = index === 0 ? `${symbol} (primero detectado)` : symbol;
        if (symbol === previous || (!previous && index === 0)) {
            option.selected = true;
        }
        startSymbolSelect.appendChild(option);
    });
}

function scheduleAutosave() {
    window.clearTimeout(autosaveTimer);
    autosaveTimer = window.setTimeout(() => saveAutosave(), 700);
}

function saveAutosave() {
    const snapshot = buildSnapshot("Autoguardado");
    localStorage.setItem(AUTOSAVE_KEY, JSON.stringify(snapshot));
}

function restoreAutosave() {
    const raw = localStorage.getItem(AUTOSAVE_KEY);
    if (!raw) {
        return false;
    }

    try {
        const snapshot = JSON.parse(raw);
        if (snapshot.version !== STORAGE_VERSION) {
            localStorage.removeItem(AUTOSAVE_KEY);
            return false;
        }
        if (!snapshot.grammar && !snapshot.inputs) {
            return false;
        }
        applySnapshot(snapshot, false);
        setStatus("Se restauro el ultimo autoguardado local.", "neutral");
        return true;
    } catch (error) {
        localStorage.removeItem(AUTOSAVE_KEY);
        return false;
    }
}

function restoreCloudImport() {
    const raw = localStorage.getItem(CLOUD_IMPORT_KEY);
    if (!raw) {
        return;
    }

    try {
        const snapshot = JSON.parse(raw);
        applySnapshot(snapshot, true);
        localStorage.removeItem(CLOUD_IMPORT_KEY);
        setStatus("Trabajo restaurado desde la biblioteca en la nube.", "success");
    } catch (error) {
        localStorage.removeItem(CLOUD_IMPORT_KEY);
    }
}

function saveSnapshot(showFeedback = false) {
    const snapshot = buildSnapshot("Version guardada");
    const history = readHistory();
    history.unshift(snapshot);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY_ITEMS)));
    saveAutosave();
    renderHistory();
    if (showFeedback) {
        setStatus("Se guardo una version en el historial local.", "success");
    }
}

async function saveCloudSnapshot() {
    if (!currentUser) {
        setAuthMessage("Inicia sesion para guardar en la base de datos.", "error");
        return;
    }

    const snapshot = buildSnapshot("Trabajo guardado");
    try {
        const response = await fetch("/api/history", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                label: snapshot.label,
                grammar: snapshot.grammar,
                inputs: snapshot.inputs,
                start_symbol: snapshot.startSymbol || null,
                derivation_mode: snapshot.derivationMode || "leftmost",
            }),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) {
            setAuthMessage(data.error?.message || "No se pudo guardar en la base de datos.", "error");
            return;
        }
        setAuthMessage("Trabajo guardado en la base de datos.", "success");
        await loadCloudHistory();
    } catch (error) {
        setAuthMessage("No se pudo conectar con el guardado en base de datos.", "error");
    }
}

function buildSnapshot(label) {
    const customTitle = workTitleInput.value.trim();
    return {
        id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`,
        version: STORAGE_VERSION,
        label: customTitle || label || buildDefaultWorkTitle(),
        grammar: grammarInput.value,
        inputs: stringsInput.value,
        startSymbol: startSymbolSelect.value || "",
        derivationMode: derivationModeSelect.value || "leftmost",
        createdAt: new Date().toISOString(),
    };
}

function readHistory() {
    try {
        return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    } catch (error) {
        localStorage.removeItem(HISTORY_KEY);
        return [];
    }
}

function renderHistory() {
    const history = readHistory();
    if (history.length === 0) {
        historyList.innerHTML = '<div class="history-empty">Todavia no hay versiones guardadas.</div>';
        return;
    }

    historyList.innerHTML = history
        .map((item) => {
            const preview = buildHistoryPreview(item);
            return `
                <article class="history-item">
                    <div class="history-meta">
                        <div>
                            <div class="history-title">${escapeHtml(item.label || "Trabajo guardado")}</div>
                            <div class="field-label compact">${escapeHtml(formatHistoryDate(item.createdAt))}</div>
                        </div>
                    </div>
                    <p class="history-preview">${escapeHtml(preview)}</p>
                    <div class="history-actions">
                        <button class="secondary-button" type="button" data-history-restore="${item.id}">Restaurar</button>
                        <button class="ghost-button" type="button" data-history-delete="${item.id}">Eliminar</button>
                    </div>
                </article>
            `;
        })
        .join("");

    historyList.querySelectorAll("[data-history-restore]").forEach((button) => {
        button.addEventListener("click", () => restoreHistoryItem(button.dataset.historyRestore));
    });

    historyList.querySelectorAll("[data-history-delete]").forEach((button) => {
        button.addEventListener("click", () => deleteHistoryItem(button.dataset.historyDelete));
    });
}

function renderCloudHistory(entries) {
    if (!currentUser) {
        cloudHistoryList.innerHTML = '<div class="history-empty">Inicia sesion para ver y guardar trabajos persistentes.</div>';
        if (cloudLibraryState) {
            cloudLibraryState.textContent = "Inicia sesion para ver tus trabajos persistentes.";
            cloudLibraryState.classList.remove("hidden");
        }
        if (cloudLibraryList) {
            cloudLibraryList.classList.add("hidden");
        }
        return;
    }
    if (entries.length === 0) {
        cloudHistoryList.innerHTML = '<div class="history-empty">Todavia no hay trabajos guardados para este usuario.</div>';
        if (cloudLibraryState) {
            cloudLibraryState.textContent = "Todavia no hay trabajos guardados para este usuario.";
            cloudLibraryState.classList.remove("hidden");
        }
        if (cloudLibraryList) {
            cloudLibraryList.classList.add("hidden");
        }
        return;
    }

    const html = entries.map((item) => `
        <article class="history-item">
            <div class="history-meta">
                <div>
                    <div class="history-title">${escapeHtml(item.label || formatHistoryDate(item.created_at))}</div>
                    <div class="field-label compact">${escapeHtml(formatHistoryDate(item.created_at))}</div>
                </div>
            </div>
            <p class="history-preview">${escapeHtml(buildHistoryPreview(item))}</p>
            <div class="history-actions">
                <button class="secondary-button" type="button" data-cloud-restore="${item.id}">Restaurar</button>
                <button class="ghost-button" type="button" data-cloud-delete="${item.id}">Eliminar</button>
            </div>
        </article>
    `).join("");

    cloudHistoryList.innerHTML = html;
    if (cloudLibraryList) {
        cloudLibraryList.innerHTML = html;
        cloudLibraryList.classList.remove("hidden");
    }
    if (cloudLibraryState) {
        cloudLibraryState.classList.add("hidden");
    }

    cloudHistoryList.querySelectorAll("[data-cloud-restore]").forEach((button) => {
        button.addEventListener("click", () => restoreCloudItem(button.dataset.cloudRestore));
    });
    cloudHistoryList.querySelectorAll("[data-cloud-delete]").forEach((button) => {
        button.addEventListener("click", () => deleteCloudItem(button.dataset.cloudDelete));
    });
    cloudLibraryList?.querySelectorAll("[data-cloud-restore]").forEach((button) => {
        button.addEventListener("click", () => restoreCloudItem(button.dataset.cloudRestore));
    });
    cloudLibraryList?.querySelectorAll("[data-cloud-delete]").forEach((button) => {
        button.addEventListener("click", () => deleteCloudItem(button.dataset.cloudDelete));
    });
}

function buildHistoryPreview(item) {
    const grammarLine = (item.grammar || "").split("\n").find((line) => line.trim()) || "Sin gramatica";
    const firstInput = (item.inputs || "").split("\n").find((line) => line.trim()) || "Sin cadenas";
    return `${grammarLine}\nEntrada: ${firstInput}`;
}

function restoreHistoryItem(id) {
    const item = readHistory().find((entry) => entry.id === id);
    if (!item) {
        return;
    }
    applySnapshot(item, true);
    setStatus("Version restaurada desde el historial local.", "success");
}

async function restoreCloudItem(id) {
    const response = await fetch("/api/history");
    const data = await response.json();
    const item = data.entries?.find((entry) => String(entry.id) === String(id));
    if (!item) {
        setAuthMessage("No se encontro el trabajo solicitado.", "error");
        return;
    }
    applySnapshot(
        {
            label: item.label || "",
            grammar: item.grammar,
            inputs: item.inputs,
            startSymbol: item.start_symbol || "",
            derivationMode: item.derivation_mode || "leftmost",
        },
        true,
    );
    setAuthMessage("Trabajo restaurado desde la base de datos.", "success");
}

function deleteHistoryItem(id) {
    const nextHistory = readHistory().filter((entry) => entry.id !== id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
    renderHistory();
    setStatus("Version eliminada del historial local.", "neutral");
}

function clearHistory() {
    localStorage.removeItem(HISTORY_KEY);
    localStorage.removeItem(AUTOSAVE_KEY);
    renderHistory();
    setStatus("Historial y autoguardado local eliminados.", "neutral");
}

async function loadCloudHistory() {
    if (!currentUser) {
        renderCloudHistory([]);
        return;
    }
    try {
        const response = await fetch("/api/history");
        const data = await response.json();
        if (!response.ok || !data.ok) {
            renderCloudHistory([]);
            setAuthMessage(data.error?.message || "No se pudo cargar el historial en base de datos.", "error");
            return;
        }
        renderCloudHistory(data.entries || []);
    } catch (error) {
        setAuthMessage("No se pudo leer el historial en base de datos.", "error");
    }
}

async function deleteCloudItem(id) {
    try {
        const response = await fetch(`/api/history/${id}`, { method: "DELETE" });
        const data = await response.json();
        if (!response.ok || !data.ok) {
            setAuthMessage(data.error?.message || "No se pudo eliminar la entrada.", "error");
            return;
        }
        setAuthMessage("Trabajo eliminado de la base de datos.", "neutral");
        await loadCloudHistory();
    } catch (error) {
        setAuthMessage("No se pudo conectar con la base de datos.", "error");
    }
}

function applySnapshot(snapshot, clearResultView) {
    workTitleInput.value = snapshot.label || "";
    grammarInput.value = snapshot.grammar || "";
    stringsInput.value = snapshot.inputs || "";
    syncStartSymbolsFromGrammar();
    if (snapshot.startSymbol) {
        startSymbolSelect.value = snapshot.startSymbol;
    }
    if (snapshot.derivationMode) {
        derivationModeSelect.value = snapshot.derivationMode;
    }
    saveAutosave();
    if (clearResultView) {
        clearResults();
    }
}

function buildDefaultWorkTitle() {
    const firstGrammarLine = grammarInput.value
        .split("\n")
        .map((line) => line.trim())
        .find((line) => line);
    if (firstGrammarLine) {
        return `Trabajo: ${firstGrammarLine.slice(0, 60)}`;
    }
    return "Trabajo guardado";
}

function formatHistoryDate(isoString) {
    const date = new Date(isoString);
    return new Intl.DateTimeFormat("es-AR", {
        dateStyle: "short",
        timeStyle: "short",
    }).format(date);
}

async function submitAuth(mode) {
    const username = authUsernameInput.value.trim();
    const password = authPasswordInput.value;
    if (!username || !password) {
        setAuthMessage("Completa usuario y contrasena.", "error");
        return;
    }

    const endpoint = mode === "register" ? "/api/auth/register" : "/api/auth/login";
    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) {
            setAuthMessage(data.error?.message || "No se pudo iniciar sesion.", "error");
            return;
        }
        currentUser = data.user;
        authPasswordInput.value = "";
        setAuthMessage(mode === "register" ? "Cuenta creada e iniciada." : "Sesion iniciada correctamente.", "success");
        syncAuthUI();
        await loadCloudHistory();
    } catch (error) {
        setAuthMessage("No se pudo conectar con el servicio de autenticacion.", "error");
    }
}

async function logoutUser() {
    await fetch("/api/auth/logout", { method: "POST" });
    currentUser = null;
    syncAuthUI();
    renderCloudHistory([]);
    setAuthMessage("Sesion cerrada.", "neutral");
}

function syncAuthUI() {
    const loggedIn = Boolean(currentUser);
    authGuestView?.classList.toggle("hidden", loggedIn);
    authUserView?.classList.toggle("hidden", !loggedIn);
    authStateBadge.textContent = loggedIn ? "Conectado" : "Invitado";
    authWelcomeText.textContent = loggedIn
        ? `Sesion iniciada como ${currentUser.username}. Tus trabajos pueden guardarse en la base de datos.`
        : "Inicia sesion para guardar tu historial en SQLite y recuperarlo desde cualquier visita local.";
}

function setAuthMessage(message, tone) {
    authMessage.textContent = message;
    authMessage.style.color =
        tone === "success" ? "var(--success)" :
        tone === "error" ? "var(--danger)" :
        "var(--muted)";
}

async function validateGrammar() {
    setStatus("Analizando gramatica y validando cadenas...", "neutral");
    validateBtn.disabled = true;
    clearGrammarError();

    try {
        const response = await fetch("/api/validate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                grammar: grammarInput.value,
                inputs: stringsInput.value,
                start_symbol: startSymbolSelect.value || null,
                derivation_mode: derivationModeSelect.value || "leftmost",
            }),
        });

        const data = await response.json();
        if (!response.ok || !data.ok) {
            if (data.error?.type === "grammar_syntax") {
                showGrammarError(data.error?.message || "La gramatica tiene un error.", data.error?.line);
            }
            renderError(data.error?.message || "No se pudo validar la gramatica.");
            setStatus("Corrige la gramatica y vuelve a intentar.", "error");
            return;
        }

        updateStartSymbols(data.available_start_symbols || []);
        startSymbolSelect.value = data.start_symbol;
        renderResults(data.results || []);
        setStatus("Validacion completada correctamente.", "success");
    } catch (error) {
        renderError("Se produjo un error inesperado al comunicarse con el servidor.");
        setStatus("No se pudo completar la solicitud.", "error");
    } finally {
        validateBtn.disabled = false;
    }
}

function clearResults() {
    resultsContainer.className = "results-empty";
    resultsContainer.textContent = "Ejecuta una validacion para ver aqui los resultados.";
}

function showGrammarError(message, lineNumber) {
    grammarInput.classList.add("has-error");
    const prefix = lineNumber ? `Linea ${lineNumber}: ` : "";
    grammarErrorHint.textContent = `${prefix}${message}`;
    grammarErrorHint.classList.remove("hidden");

    if (lineNumber) {
        focusGrammarLine(lineNumber);
    } else {
        grammarInput.focus();
    }
}

function clearGrammarError() {
    grammarInput.classList.remove("has-error");
    grammarErrorHint.textContent = "";
    grammarErrorHint.classList.add("hidden");
}

function focusGrammarLine(lineNumber) {
    const lines = grammarInput.value.split("\n");
    const safeLine = Math.max(1, Math.min(lineNumber, lines.length));
    let start = 0;
    for (let index = 0; index < safeLine - 1; index += 1) {
        start += lines[index].length + 1;
    }
    const lineText = lines[safeLine - 1] || "";
    const end = start + lineText.length;

    grammarInput.focus();
    grammarInput.setSelectionRange(start, end);

    const lineHeight = parseFloat(window.getComputedStyle(grammarInput).lineHeight) || 24;
    grammarInput.scrollTop = Math.max(0, (safeLine - 2) * lineHeight);
}

function renderError(message) {
    resultsContainer.className = "";
    resultsContainer.innerHTML = `<div class="error-banner">${escapeHtml(message)}</div>`;
}

function renderResults(results) {
    if (results.length === 0) {
        resultsContainer.className = "results-empty";
        resultsContainer.textContent = "No hubo cadenas para evaluar. Las lineas vacias se ignoran; usa ε si quieres probar la cadena vacia.";
        return;
    }

    resultsContainer.className = "";
    resultsContainer.innerHTML = results
        .map((result) => {
            const normalizedInput = result.input === "" ? "ε" : escapeHtml(result.input);
            const derivationHtml = result.accepted && result.derivation?.length
                ? `
                    <div class="detail-block">
                        <h3>${formatDerivationType(result.derivation_type)}</h3>
                        <ol class="detail-list">
                            ${result.derivation.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}
                        </ol>
                    </div>
                `
                : "";
            const treeHtml = result.accepted && result.tree
                ? `
                    <div class="detail-block">
                        <h3>Arbol de parsing</h3>
                        <div class="parse-tree">${renderTree(result.tree)}</div>
                    </div>
                `
                : "";

            return `
                <article class="result-card">
                    <div class="result-header">
                        <div class="result-input">${normalizedInput}</div>
                        <span class="badge ${result.accepted ? "accepted" : "rejected"}">
                            ${result.accepted ? "Pertenece" : "No pertenece"}
                        </span>
                    </div>
                    <p class="result-message">${escapeHtml(result.message)}</p>
                    ${derivationHtml}
                    ${treeHtml}
                </article>
            `;
        })
        .join("");
}

function renderTree(node) {
    if (!node) {
        return "";
    }

    const layout = buildTreeLayout(node);
    const connectors = layout.edges.map((edge) => {
        const elbowY = edge.fromY + (edge.toY - edge.fromY) * 0.45;
        return `
            <path
                d="M ${edge.fromX} ${edge.fromY} L ${edge.fromX} ${elbowY} L ${edge.toX} ${elbowY} L ${edge.toX} ${edge.toY}"
                class="tree-edge"
            />
        `;
    }).join("");

    const nodes = layout.nodes.map((item) => {
        const symbol = escapeHtml(item.node.symbol || "ε");
        const nodeClass = item.node.is_terminal ? "tree-svg-node terminal" : "tree-svg-node non-terminal";
        const textClass = item.node.is_terminal ? "tree-svg-label terminal" : "tree-svg-label non-terminal";
        return `
            <g class="${nodeClass}">
                <rect
                    x="${item.left}"
                    y="${item.top}"
                    width="${item.width}"
                    height="${item.height}"
                    rx="${item.radius}"
                    ry="${item.radius}"
                />
                <text
                    class="${textClass}"
                    x="${item.centerX}"
                    y="${item.centerY}"
                    dominant-baseline="middle"
                    text-anchor="middle"
                >
                    ${symbol}
                </text>
            </g>
        `;
    }).join("");

    return `
        <svg
            class="parse-tree-svg"
            viewBox="0 0 ${layout.width} ${layout.height}"
            width="${layout.width}"
            height="${layout.height}"
            preserveAspectRatio="xMidYMin meet"
            aria-hidden="true"
        >
            ${connectors}
            ${nodes}
        </svg>
    `;
}

function buildTreeLayout(root) {
    const config = {
        leafSpacing: 86,
        siblingGap: 18,
        levelGap: 92,
        topPadding: 18,
        sidePadding: 28,
        nodeHeight: 48,
        minNodeWidth: 62,
        charWidth: 10,
        horizontalPadding: 30,
        nodeRadius: 16,
    };

    function estimateNodeWidth(symbol) {
        const label = symbol || "ε";
        return Math.max(config.minNodeWidth, label.length * config.charWidth + config.horizontalPadding);
    }

    const nodes = [];
    const edges = [];
    let maxDepth = 0;
    let currentLeafX = config.sidePadding;

    function placeSubtree(node, depth) {
        maxDepth = Math.max(maxDepth, depth);
        const top = config.topPadding + depth * config.levelGap;
        const nodeWidth = estimateNodeWidth(node.symbol);
        const children = node.children || [];

        if (children.length === 0) {
            const centerX = currentLeafX + nodeWidth / 2;
            currentLeafX += Math.max(config.leafSpacing, nodeWidth + config.siblingGap);
            const left = centerX - nodeWidth / 2;
            const centerY = top + config.nodeHeight / 2;
            nodes.push({
                node,
                left,
                top,
                width: nodeWidth,
                height: config.nodeHeight,
                radius: config.nodeRadius,
                centerX,
                centerY,
            });
            return { centerX, left, right: left + nodeWidth };
        }

        const childLayouts = children.map((child) => placeSubtree(child, depth + 1));
        const firstChild = childLayouts[0];
        const lastChild = childLayouts[childLayouts.length - 1];
        const centerX = (firstChild.centerX + lastChild.centerX) / 2;
        const left = centerX - nodeWidth / 2;
        const centerY = top + config.nodeHeight / 2;

        nodes.push({
            node,
            left,
            top,
            width: nodeWidth,
            height: config.nodeHeight,
            radius: config.nodeRadius,
            centerX,
            centerY,
        });

        childLayouts.forEach((childLayout) => {
            edges.push({
                fromX: centerX,
                fromY: top + config.nodeHeight,
                toX: childLayout.centerX,
                toY: config.topPadding + (depth + 1) * config.levelGap,
            });
        });

        return {
            centerX,
            left: Math.min(left, firstChild.left),
            right: Math.max(left + nodeWidth, lastChild.right),
        };
    }

    const rootLayout = placeSubtree(root, 0);
    const minLeft = Math.min(...nodes.map((item) => item.left), rootLayout.left);
    const maxRight = Math.max(...nodes.map((item) => item.left + item.width), rootLayout.right);
    const shiftX = minLeft < config.sidePadding ? config.sidePadding - minLeft : 0;

    if (shiftX !== 0) {
        nodes.forEach((item) => {
            item.left += shiftX;
            item.centerX += shiftX;
        });
        edges.forEach((edge) => {
            edge.fromX += shiftX;
            edge.toX += shiftX;
        });
    }

    const width = maxRight + shiftX + config.sidePadding;

    return {
        width,
        height: config.topPadding + maxDepth * config.levelGap + config.nodeHeight + 24,
        nodes,
        edges,
    };
}

function setStatus(message, tone) {
    statusMessage.textContent = message;
    statusMessage.style.color =
        tone === "success" ? "var(--success)" :
        tone === "error" ? "var(--danger)" :
        "var(--muted)";
}

function formatDerivationType(type) {
    if (type === "rightmost") {
        return "Derivacion por la derecha";
    }
    return "Derivacion por la izquierda";
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function cleanupLegacyStorage() {
    [
        "bnf-validator-autosave",
        "bnf-validator-history",
        "bnf-validator-autosave-v1",
        "bnf-validator-history-v1",
    ].forEach((key) => localStorage.removeItem(key));
}

init();
