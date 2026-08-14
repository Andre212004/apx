const icon = (name) => `assets/icons/${name}.svg`;
const browserErrors = [];
window.addEventListener("error", (event) => browserErrors.push(event.message));
window.addEventListener("unhandledrejection", (event) => browserErrors.push(String(event.reason)));

let environments = [
  { id: "hub", name: "Hub", icon: "apx", detail: "Centro APX", state: "ready" },
  { id: "university", name: "Universidade", icon: "university", detail: "Estudo e aulas", state: "ready" },
  { id: "games", name: "Jogos", icon: "games", detail: "Jogos e lazer", state: "ready" },
  { id: "development", name: "Desenvolvimento", icon: "development", detail: "Código e testes", state: "warning" },
  { id: "private", name: "Privado", icon: "private", detail: "Alta segurança", state: "ready" },
];

const apxButton = document.querySelector("#apx-button");
const switcher = document.querySelector("#environment-switcher");
const environmentList = document.querySelector("#environment-list");
const contextMenu = document.querySelector("#context-menu");
const transitionDialog = document.querySelector("#transition-dialog");
const transitionName = document.querySelector("#transition-name");
const confirmDialog = document.querySelector("#confirm-dialog");
const confirmTitle = document.querySelector("#confirm-title");
const confirmCopy = document.querySelector("#confirm-copy");
const confirmAction = document.querySelector("#confirm-action");
const createDialog = document.querySelector("#create-dialog");
const createForm = document.querySelector("#create-form");
const managementView = document.querySelector("#management-view");
const managementList = document.querySelector("#management-list");
const environmentCount = document.querySelector("#environment-count");
const toast = document.querySelector("#toast");

function renderSwitcher() {
  environmentList.replaceChildren(...environments.slice(0, 5).map((environment) => {
    const button = document.createElement("button");
    button.className = "environment-choice";
    button.dataset.environment = environment.id;
    button.innerHTML = `<img src="${icon(environment.icon)}" alt=""><strong>${environment.name}</strong><i class="state-dot ${environment.state === "warning" ? "warning" : ""}" aria-label="${environment.state === "warning" ? "Precisa de verificação" : "Pronto"}"></i>`;
    button.addEventListener("click", () => chooseEnvironment(environment));
    button.addEventListener("contextmenu", (event) => showEnvironmentMenu(event, environment));
    button.addEventListener("keydown", (event) => {
      if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) showEnvironmentMenu(event, environment);
    });
    return button;
  }));
}

function renderManagement() {
  environmentCount.textContent = `${environments.length} espaços`;
  managementList.replaceChildren(...environments.map((environment) => {
    const row = document.createElement("article");
    row.className = "management-row";
    const primaryLabel = environment.state === "warning" ? "Verificar" : "Abrir";
    const primaryClass = environment.state === "warning" ? "warning" : "primary";
    row.innerHTML = `<img src="${icon(environment.icon)}" alt=""><div class="row-title"><strong>${environment.name}</strong><span>${environment.detail}</span></div><div class="row-state"><strong>${environment.state === "warning" ? "Verificar antes de abrir" : "Tudo pronto"}</strong><small>${environment.state === "warning" ? "Apenas verificações disponíveis" : "Isolado e protegido — demonstração"}</small></div><div class="row-actions"><button class="details">Detalhes</button><button class="${primaryClass}">${primaryLabel}</button></div>`;
    row.querySelector(`.${primaryClass}`).addEventListener("click", () => environment.state === "warning" ? verifyEnvironment(environment) : chooseEnvironment(environment));
    row.querySelector(".details").addEventListener("click", (event) => showEnvironmentMenu(event, environment));
    return row;
  }));
}

function toggleSwitcher(force) {
  hideContextMenu();
  const shouldOpen = force ?? switcher.hidden;
  switcher.hidden = !shouldOpen;
  apxButton.setAttribute("aria-expanded", String(shouldOpen));
  if (shouldOpen) switcher.querySelector("button")?.focus();
}

function menuButton(label, iconName, handler, danger = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.setAttribute("role", "menuitem");
  if (danger) button.className = "danger";
  button.innerHTML = `<img src="${icon(iconName)}" alt="">${label}`;
  button.addEventListener("click", () => { hideContextMenu(); handler(); });
  return button;
}

function showMenuAt(x, y, items) {
  contextMenu.replaceChildren(...items);
  contextMenu.hidden = false;
  const width = 250;
  const height = items.length * 44 + 16;
  contextMenu.style.left = `${Math.min(x, innerWidth - width - 12)}px`;
  contextMenu.style.top = `${Math.min(y, innerHeight - height - 92)}px`;
  contextMenu.querySelector("button")?.focus();
}

function showApxMenu(event) {
  event.preventDefault();
  toggleSwitcher(false);
  const rect = apxButton.getBoundingClientRect();
  showMenuAt(rect.left - 80, rect.top - 190, [
    menuButton("Criar novo Environment", "new", () => createDialog.showModal()),
    menuButton("Ver arquivados", "archive", () => openManagement("archived")),
    menuButton("Abrir gestão completa", "details", () => openManagement()),
  ]);
}

function showEnvironmentMenu(event, environment) {
  event.preventDefault();
  event.stopPropagation();
  const safeItems = environment.state === "warning" ? [
    menuButton("Verificar novamente", "refresh", () => verifyEnvironment(environment)),
    menuButton("Ver detalhes", "details", () => openManagement()),
  ] : [
    menuButton("Abrir", environment.icon, () => chooseEnvironment(environment)),
    menuButton("Criar ponto de recuperação", "refresh", () => notify(`Ponto de recuperação simulado para ${environment.name}.`)),
    menuButton("Arquivar", "archive", () => notify(`${environment.name} seria arquivado.`)),
    menuButton("Ver detalhes", "details", () => openManagement()),
    menuButton("Apagar…", "delete", () => requestDelete(environment), true),
  ];
  showMenuAt(event.clientX || innerWidth / 2, event.clientY || innerHeight / 2, safeItems);
}

function chooseEnvironment(environment) {
  if (environment.state === "warning") {
    verifyEnvironment(environment);
    return;
  }
  toggleSwitcher(false);
  transitionName.textContent = environment.name;
  transitionDialog.showModal();
  setTimeout(() => {
    transitionDialog.close();
    notify(`Demonstração: entrarias em ${environment.name}.`);
  }, 900);
}

function verifyEnvironment(environment) {
  toggleSwitcher(false);
  notify(`${environment.name} precisa de uma verificação antes de poder abrir.`);
}

function requestDelete(environment) {
  confirmTitle.textContent = `Apagar “${environment.name}”?`;
  confirmCopy.textContent = "Num APX real, esta ação apagaria os programas e ficheiros deste Environment após confirmação forte. Aqui remove apenas o cartão temporário.";
  confirmAction.onclick = () => {
    environments = environments.filter((item) => item.id !== environment.id);
    renderSwitcher();
    renderManagement();
    notify(`${environment.name} removido apenas da demonstração.`);
  };
  confirmDialog.showModal();
}

function openManagement(mode = "environments") {
  toggleSwitcher(false);
  hideContextMenu();
  managementView.hidden = false;
  document.querySelector("#archived-nav").classList.toggle("active", mode === "archived");
  managementView.querySelector("nav button:first-child").classList.toggle("active", mode !== "archived");
  renderManagement();
  document.querySelector("#close-management").focus();
}

function hideContextMenu() { contextMenu.hidden = true; }
function notify(message) {
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(notify.timeout);
  notify.timeout = setTimeout(() => { toast.hidden = true; }, 2400);
}

apxButton.addEventListener("click", () => toggleSwitcher());
apxButton.addEventListener("contextmenu", showApxMenu);
document.addEventListener("click", (event) => { if (!contextMenu.contains(event.target)) hideContextMenu(); });
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") { toggleSwitcher(false); hideContextMenu(); if (!managementView.hidden) managementView.hidden = true; }
  if (event.key === "ContextMenu" && document.activeElement === apxButton) showApxMenu(event);
});
document.querySelector("#close-management").addEventListener("click", () => { managementView.hidden = true; apxButton.focus(); });
document.querySelector("#management-create").addEventListener("click", () => createDialog.showModal());
document.querySelector("#archived-nav").addEventListener("click", () => notify("Não existem Environments arquivados nesta demonstração."));

createForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(createForm);
  const selectedTemplate = data.get("template");
  const name = document.querySelector("#environment-name").value.trim();
  const followsHostUpdates = data.get("followHostUpdates") === "on";
  if (!name) return;
  const iconName = selectedTemplate === "Jogos" ? "games" : selectedTemplate === "Desenvolvimento" ? "development" : "university";
  environments.push({ id: `demo-${Date.now()}`, name, icon: iconName,
    detail: `Modelo ${selectedTemplate} · updates ${followsHostUpdates ? "coordenados" : "excluídos"}`,
    state: "ready", followsHostUpdates });
  createDialog.close();
  renderSwitcher();
  renderManagement();
  notify(`${name} criado apenas como demonstração.`);
});

function runBrowserSelfTest() {
  const results = [];
  apxButton.click();
  results.push(["left-click-opens-five", !switcher.hidden && environmentList.children.length === 5]);
  apxButton.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, clientX: 700, clientY: 800 }));
  results.push(["right-click-apx-menu", !contextMenu.hidden && contextMenu.textContent.includes("Criar novo Environment")]);
  hideContextMenu();
  toggleSwitcher(true);
  const university = environmentList.querySelector('[data-environment="university"]');
  university.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, clientX: 700, clientY: 500 }));
  results.push(["right-click-environment-menu", !contextMenu.hidden && contextMenu.textContent.includes("Apagar")]);
  hideContextMenu();
  openManagement();
  results.push(["management-view-opens", !managementView.hidden && managementList.children.length === environments.length]);
  managementView.hidden = true;
  document.body.dataset.selftest = results.every(([, passed]) => passed) ? "passed" : "failed";
  document.body.dataset.consoleErrors = String(browserErrors.length);
  const output = document.createElement("pre");
  output.id = "selftest-results";
  output.textContent = JSON.stringify(Object.fromEntries(results));
  document.body.append(output);
}

renderSwitcher();
renderManagement();
if (new URLSearchParams(location.search).get("state") === "open") toggleSwitcher(true);
if (new URLSearchParams(location.search).get("state") === "management") openManagement();
if (new URLSearchParams(location.search).get("selftest") === "1") runBrowserSelfTest();
