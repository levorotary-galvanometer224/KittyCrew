const state = {
  crews: [],
  avatars: [],
  providers: [],
  skills: [],
  siteTheme: "candy-soft",
  globalSkills: [],
  memberNameCandidates: [],
  providerModels: {},
  providerModelsFetchedAt: {},
  activeCrewId: null,
  activeAvatarMemberId: null,
  activeMemberProvider: "",
  editingCrewId: null,
  editingMemberId: null,
  editingMemberScope: null,
  crewNameDraft: "",
  memberNameDraft: "",
  memberTitleDraft: "",
  memberWorkingDirDraft: "",
  memberWorkingDirAuto: "",
  memberWorkingDirTouched: false,
  memberSkillSelections: [],
  memberSkillCustom: "",
  activeSkillMemberId: null,
  skillModalSelections: [],
  skillModalCustom: "",
  globalSettingsThemeDraft: "candy-soft",
  globalSkillSelections: [],
  globalSkillCustom: "",
  projectRoot: "",
  activeExpandedMemberId: null,
  composerDrafts: {},
  memberQueues: {},
};

const SITE_THEMES = [
  { id: "candy-soft", label: "Candy Soft", description: "The current pastel control room." },
  { id: "sunset-pop", label: "Sunset Pop", description: "Warm coral gradients and punchier contrast." },
  { id: "mint-garden", label: "Mint Garden", description: "Fresh greens with airy card tones." },
  { id: "midnight-ink", label: "Midnight Ink", description: "Dark navy surfaces with crisp highlights." },
  { id: "peach-cream", label: "Peach Cream", description: "Soft peach cards and bright paper tones." },
];

const pendingMembers = new Set();
const memberStreams = new Map();
const providerModelLoads = new Map();

const crewList = document.querySelector("#crew-list");
const addCrewButton = document.querySelector("#add-crew-button");
const globalSettingsButton = document.querySelector("#global-settings-button");
const globalSettingsModal = document.querySelector("#global-settings-modal");
const themeOptions = document.querySelector("#theme-options");
const globalSkillSelected = document.querySelector("#global-skill-selected");
const globalSkillOptions = document.querySelector("#global-skill-options");
const globalSkillCustomInput = document.querySelector("#global-skill-custom");
const globalSkillAddButton = document.querySelector("#global-skill-add-button");
const globalSettingsSaveButton = document.querySelector("#global-settings-save-button");
const memberModal = document.querySelector("#member-modal");
const providerOptions = document.querySelector("#provider-options");
const memberTitleInput = document.querySelector("#member-title");
const memberWorkingDirInput = document.querySelector("#member-working-dir");
const memberSkillOptions = document.querySelector("#member-skill-options");
const memberCreateSelected = document.querySelector("#member-create-selected");
const memberSkillCustomInput = document.querySelector("#member-skill-custom");
const memberSkillAddButton = document.querySelector("#member-skill-add-button");
const memberCreateButton = document.querySelector("#member-create-button");
const skillModal = document.querySelector("#skill-modal");
const skillModalOptions = document.querySelector("#skill-modal-options");
const memberSkillSelected = document.querySelector("#member-skill-selected");
const skillModalCustomInput = document.querySelector("#skill-modal-custom");
const skillModalAddButton = document.querySelector("#skill-modal-add-button");
const skillModalSaveButton = document.querySelector("#skill-modal-save-button");
const avatarModal = document.querySelector("#avatar-modal");
const avatarOptions = document.querySelector("#avatar-options");
const expandedMemberModal = document.querySelector("#expanded-member-modal");
const expandedMemberContent = document.querySelector("#expanded-member-content");
const toast = document.querySelector("#toast");

let toastTimer = null;

const DEFAULT_MEMBER_NAME_CANDIDATES = [
  "Mochi Whiskers",
  "Poppy Paws",
  "Luna Biscuit",
  "Milo Mittens",
  "Clover Tail",
  "Pepper Purr",
  "Nori Buttons",
  "Olive Tuft",
  "Maple Socks",
  "Sunny Pebble",
  "Coco Nibbles",
  "Pumpkin Bloom",
  "Hazel Puff",
  "Teddy Marmalade",
  "Pippa Velvet",
  "Basil Toes",
  "Waffle Nose",
  "Daisy Curls",
  "Benny Whisk",
  "Rosie Pounce",
  "Toffee Paws",
  "Juniper Bean",
  "Archie Fluff",
  "Mabel Mews",
  "Otis Dandelion",
  "Ivy Snuggle",
  "Mango Tumble",
  "Ruby Sprout",
  "Finn Clover",
  "Maisie Purr",
  "Biscuit Hop",
  "Nala Trinket",
  "Toby Patches",
  "Willow Pebbles",
  "Freya Nuzzle",
  "Theo Buttercup",
  "Penny Winks",
  "Remy Fuzz",
  "Millie Buttons",
  "Leo Tinsel",
  "Zoe Marzipan",
  "Alfie Twirl",
  "Bonnie Whimsy",
  "Jasper Mallow",
  "Honey Sable",
  "Louie Pip",
  "Piper Trinket",
  "Chester Purrkins",
  "Elsie Tofu",
  "Murphy Velvet",
  "Skye Pudding",
  "Gus Acorn",
  "Tilly Crumbs",
  "Hugo Bramble",
  "Suki Petal",
  "Walter Waffles",
  "Dolly Fable",
  "Rory Pebble",
  "Phoebe Tinsel",
  "Benny Marshmallow",
  "Minnie Thimble",
  "Ollie Pompom",
  "Sadie Plume",
  "Harvey Button",
  "Pru Feather",
  "Rufus Noodle",
  "Nina Pickles",
  "Cosmo Pawsley",
  "Bea Tumble",
  "Ginger Dot",
  "Percy Muffin",
  "Winnie Purrl",
  "Felix Wisp",
  "Dotty Maple",
  "Cleo Snickers",
  "Bruno Pecan",
  "Birdie Bubbles",
  "Ralph Custard",
  "Indie Fawn",
  "Mimi Pockets",
  "Bodhi Tater",
  "Cali Twinkle",
  "Ozzy Buttons",
  "Nellie Moss",
  "Kiki Sherbet",
  "Maxie Purrcy",
  "Dottie Tofu",
  "Sage Pollen",
  "Rocco Biscotti",
  "Lottie Pawsworth",
  "Yuki Crumpet",
  "Trixie Meringue",
  "Juno Whispurr",
  "Bambi Chestnut",
  "Frankie Popcorn",
  "Marnie Nuzzles",
  "Ziggy Paws",
  "Evie Butterbean",
  "Koda Whiskers",
  "Pixie Tart",
];

document.addEventListener("DOMContentLoaded", () => {
  bindGlobalEvents();
  refreshState().catch((error) => showToast(error.message));
});

function bindGlobalEvents() {
  globalSettingsButton.addEventListener("click", () => openGlobalSettingsModal());

  addCrewButton.addEventListener("click", async () => {
    addCrewButton.disabled = true;
    try {
      await request("/api/crews", { method: "POST" });
      await refreshState();
    } catch (error) {
      showToast(error.message);
    } finally {
      addCrewButton.disabled = false;
    }
  });

  memberModal.addEventListener("click", (event) => {
    if (event.target === memberModal || event.target.dataset.closeModal === "member") {
      closeMemberModal();
    }
  });

  globalSettingsModal.addEventListener("click", (event) => {
    if (event.target === globalSettingsModal || event.target.dataset.closeModal === "global-settings") {
      closeGlobalSettingsModal();
    }
  });

  avatarModal.addEventListener("click", (event) => {
    if (event.target === avatarModal || event.target.dataset.closeModal === "avatar") {
      closeAvatarModal();
    }
  });

  expandedMemberModal.addEventListener("click", (event) => {
    if (event.target === expandedMemberModal || event.target.dataset.closeModal === "expanded-member") {
      closeExpandedMemberModal();
    }
  });

  skillModal.addEventListener("click", (event) => {
    if (event.target === skillModal || event.target.dataset.closeModal === "skill") {
      closeSkillModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    closeMemberModal();
    closeGlobalSettingsModal();
    closeSkillModal();
    closeAvatarModal();
    closeExpandedMemberModal();
  });

  memberTitleInput.addEventListener("input", (event) => {
    const previousAuto = state.memberWorkingDirAuto;
    state.memberTitleDraft = event.target.value;
    state.memberWorkingDirAuto = buildDefaultMemberWorkingDir(state.projectRoot, state.memberTitleDraft);
    if (!state.memberWorkingDirTouched || state.memberWorkingDirDraft === previousAuto) {
      state.memberWorkingDirDraft = state.memberWorkingDirAuto;
      memberWorkingDirInput.value = state.memberWorkingDirDraft;
      state.memberWorkingDirTouched = false;
    }
  });

  memberWorkingDirInput.addEventListener("input", (event) => {
    state.memberWorkingDirDraft = event.target.value;
    state.memberWorkingDirTouched = state.memberWorkingDirDraft !== state.memberWorkingDirAuto;
  });

  memberSkillCustomInput.addEventListener("input", (event) => {
    state.memberSkillCustom = event.target.value;
    renderCreateSkillOptions();
  });

  memberSkillAddButton.addEventListener("click", () => {
    addCreateSkillSelection(resolveSkillReference(state.memberSkillCustom.trim(), state.globalSkills));
  });

  skillModalCustomInput.addEventListener("input", (event) => {
    state.skillModalCustom = event.target.value;
    renderSkillModal();
  });

  skillModalAddButton.addEventListener("click", () => {
    addSkillModalSelection(resolveSkillReference(state.skillModalCustom.trim(), state.globalSkills));
  });

  globalSkillCustomInput.addEventListener("input", (event) => {
    state.globalSkillCustom = event.target.value;
    renderGlobalSettingsModal();
  });

  globalSkillAddButton.addEventListener("click", () => {
    addGlobalSkillSelection(resolveSkillReference(state.globalSkillCustom.trim(), state.skills));
  });

  memberSkillCustomInput.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") {
      return;
    }
    event.preventDefault();
    addCreateSkillSelection(resolveSkillReference(state.memberSkillCustom.trim(), state.globalSkills));
  });

  skillModalCustomInput.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") {
      return;
    }
    event.preventDefault();
    addSkillModalSelection(resolveSkillReference(state.skillModalCustom.trim(), state.globalSkills));
  });

  globalSkillCustomInput.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") {
      return;
    }
    event.preventDefault();
    addGlobalSkillSelection(resolveSkillReference(state.globalSkillCustom.trim(), state.skills));
  });

  skillModalSaveButton.addEventListener("click", async () => {
    if (!state.activeSkillMemberId) {
      return;
    }

    skillModalSaveButton.disabled = true;
    try {
      const payload = await request(`/api/members/${state.activeSkillMemberId}/skills`, {
        method: "PATCH",
        body: { skill_references: state.skillModalSelections },
      });
      patchMember(payload.member);
      closeSkillModal();
      render();
    } catch (error) {
      showToast(error.message);
    } finally {
      skillModalSaveButton.disabled = false;
    }
  });

  globalSettingsSaveButton.addEventListener("click", async () => {
    globalSettingsSaveButton.disabled = true;
    try {
      const payload = await request("/api/settings", {
        method: "PATCH",
        body: {
          site_theme: state.globalSettingsThemeDraft,
          global_skill_references: state.globalSkillSelections,
        },
      });
      applyBootstrap(payload);
      closeGlobalSettingsModal();
      render();
    } catch (error) {
      showToast(error.message);
    } finally {
      globalSettingsSaveButton.disabled = false;
    }
  });

  memberCreateButton.addEventListener("click", async () => {
    if (!state.activeCrewId) {
      return;
    }
    if (!state.activeMemberProvider) {
      showToast("Choose a provider first.");
      return;
    }

    const workingDir = state.memberWorkingDirDraft.trim();
    const title = state.memberTitleDraft.trim();
    if (!title) {
      showToast("Member name cannot be empty.");
      return;
    }
    if (!workingDir) {
      showToast("Working directory cannot be empty.");
      return;
    }

    memberCreateButton.disabled = true;
    try {
      await request(`/api/crews/${state.activeCrewId}/members`, {
        method: "POST",
        body: {
          provider: state.activeMemberProvider,
          title,
          working_dir: workingDir,
          skill_references: state.memberSkillSelections,
        },
      });
      closeMemberModal();
      await refreshState();
    } catch (error) {
      showToast(error.message);
    } finally {
      memberCreateButton.disabled = false;
    }
  });
}

async function refreshState() {
  const data = await request("/api/state");
  applyBootstrap(data);
  render();
}

function applyBootstrap(data) {
  state.crews = data.state?.crews ?? [];
  state.siteTheme = data.state?.site_theme ?? "candy-soft";
  state.globalSkills = data.state?.global_skills ?? [];
  state.avatars = data.avatars;
  state.providers = data.providers;
  state.skills = data.skills ?? [];
  state.memberNameCandidates = data.member_name_candidates ?? DEFAULT_MEMBER_NAME_CANDIDATES;
  state.projectRoot = data.project_root ?? "";
  applySiteTheme(state.siteTheme);
}

function applySiteTheme(themeId) {
  if (!document.body?.dataset) {
    return;
  }
  document.body.dataset.theme = themeId || "candy-soft";
}

function render() {
  const interactionState = captureMemberInteractionState(document.activeElement);
  const chatScrollState = captureChatScrollState(document.querySelectorAll(".chat-log"));
  renderCrews();
  renderGlobalSettingsModal();
  renderProviderOptions();
  renderCreateSkillOptions();
  renderSkillModal();
  renderAvatarOptions();
  renderExpandedMemberModal();
  restoreChatScrollState(chatScrollState, locateChatScrollTarget);
  restoreMemberInteractionState(interactionState, locateMemberInteractionTarget);
}

function renderCrews() {
  crewList.replaceChildren();

  if (state.crews.length === 0) {
    const emptyState = document.createElement("section");
    emptyState.className = "empty-state";

    const title = document.createElement("h2");
    title.textContent = "No crews yet";

    const copy = document.createElement("p");
    copy.textContent = "Tap the big plus at the bottom to create your first crew, then start adding catty little agent sessions.";

    emptyState.append(title, copy);
    crewList.append(emptyState);
    return;
  }

  for (const crew of state.crews) {
    crewList.append(createCrewElement(crew));
  }
}

function getUsedMemberTitles(crews) {
  return crews.flatMap((crew) => crew.members.map((member) => member.title));
}

function normalizeMemberName(value) {
  return String(value ?? "").trim().replace(/\s+/g, " ");
}

function normalizeMemberNameKey(value) {
  return normalizeMemberName(value).toLowerCase();
}

export function pickAvailableMemberName(
  usedNames,
  offset = Date.now(),
  candidates = DEFAULT_MEMBER_NAME_CANDIDATES,
) {
  const used = new Set(usedNames.map((name) => normalizeMemberNameKey(name)));
  const available = candidates.filter((name) => !used.has(normalizeMemberNameKey(name)));
  if (available.length === 0) {
    return "";
  }
  const startIndex = Math.abs(Number(offset) || 0) % available.length;
  return available[startIndex];
}

export function buildDefaultMemberWorkingDir(projectRoot, title) {
  const root = "/tmp/KittyCrew";
  const normalizedTitle = normalizeMemberName(title);
  const slug = normalizedTitle.replace(/[\\/]+/g, "-").replace(/\s+/g, "-").replace(/^[.\s-]+|[.\s-]+$/g, "") || "member";
  return `${root}/${slug}`;
}

export function isMemberInteractionLocked(runtimeState, memberId, expanded) {
  return false;
}

function createCrewElement(crew) {
  const section = document.createElement("section");
  section.className = "crew-panel";

  const header = document.createElement("div");
  header.className = "crew-header";

  const intro = document.createElement("div");

  const kicker = document.createElement("p");
  kicker.className = "crew-kicker";
  kicker.textContent = "Crew stack";

  const nameBlock = createCrewNameBlock(crew);

  intro.append(kicker, nameBlock);

  const actions = document.createElement("div");
  actions.className = "crew-actions";

  const count = document.createElement("span");
  count.className = "crew-count";
  count.textContent = `${crew.members.length}/5 members`;

  const addButton = document.createElement("button");
  addButton.className = "action-pill";
  addButton.type = "button";
  addButton.textContent = "+ Add member";
  addButton.disabled = crew.members.length >= 5;
  addButton.addEventListener("click", () => openMemberModal(crew.id));

  const deleteButton = document.createElement("button");
  deleteButton.className = "icon-chip icon-chip--danger";
  deleteButton.type = "button";
  deleteButton.title = "Delete crew";
  deleteButton.textContent = "Delete crew";
  deleteButton.addEventListener("click", async () => {
    const confirmed = window.confirm(`Delete ${crew.name}? This will close every member session in this crew.`);
    if (!confirmed) {
      return;
    }

    try {
      await request(`/api/crews/${crew.id}`, { method: "DELETE" });
      clearCrewRuntime(crew);
      await refreshState();
    } catch (error) {
      showToast(error.message);
    }
  });

  actions.append(count, addButton, deleteButton);
  header.append(intro, actions);

  const strip = document.createElement("div");
  strip.className = "member-strip";

  if (crew.members.length === 0) {
    const emptySlot = document.createElement("div");
    emptySlot.className = "empty-member-slot";
    const title = document.createElement("h3");
    title.textContent = "Fresh crew, zero cats";
    const copyText = document.createElement("p");
    copyText.textContent = "Use the plus button to create the first member session inside this crew.";
    const quickAdd = document.createElement("button");
    quickAdd.className = "member-add-button";
    quickAdd.type = "button";
    quickAdd.textContent = "+";
    quickAdd.addEventListener("click", () => openMemberModal(crew.id));
    emptySlot.append(quickAdd, title, copyText);
    strip.append(emptySlot);
  }

  for (const member of crew.members) {
    strip.append(createMemberElement(member));
  }

  if (crew.members.length > 0 && crew.members.length < 5) {
    const addCard = document.createElement("div");
    addCard.className = "member-add-card";
    const addMemberButton = document.createElement("button");
    addMemberButton.className = "member-add-button";
    addMemberButton.type = "button";
    addMemberButton.textContent = "+";
    addMemberButton.addEventListener("click", () => openMemberModal(crew.id));
    const title = document.createElement("h3");
    title.textContent = "Another teammate";
    const copyText = document.createElement("p");
    copyText.textContent = "Create one more member card and lock in its provider type.";
    addCard.append(addMemberButton, title, copyText);
    strip.append(addCard);
  }

  section.append(header, strip);
  return section;
}

function createMemberElement(member, { expanded = false } = {}) {
  const article = document.createElement("article");
  article.className = "member-card";
  if (expanded) {
    article.classList.add("member-card--expanded");
  }
  article.dataset.memberId = member.id;

  const avatar = avatarMap().get(member.avatar_id);
  const provider = providerMap().get(member.provider);
  const currentStatus = pendingMembers.has(member.id) ? "thinking" : member.status;
  const interactionLocked = isMemberInteractionLocked(state, member.id, expanded);

  const actions = document.createElement("div");
  actions.className = "member-card__actions";

  const expandButton = document.createElement("button");
  expandButton.className = "member-card__action member-card__action--expand";
  expandButton.type = "button";
  expandButton.title = expanded ? `Collapse ${member.title}` : `Expand ${member.title}`;
  expandButton.setAttribute("aria-label", expanded ? `Collapse ${member.title}` : `Expand ${member.title}`);
  expandButton.textContent = expanded ? "−" : "□";
  expandButton.disabled = interactionLocked;
  expandButton.addEventListener("click", () => {
    if (expanded) {
      closeExpandedMemberModal();
      return;
    }
    openExpandedMemberModal(member.id);
  });

  const removeButton = document.createElement("button");
  removeButton.className = "member-card__action member-card__action--close";
  removeButton.type = "button";
  removeButton.title = `Delete ${member.title}`;
  removeButton.setAttribute("aria-label", `Delete ${member.title}`);
  removeButton.textContent = "×";
  removeButton.disabled = interactionLocked;
  removeButton.addEventListener("click", async () => {
    const confirmed = window.confirm(`Delete ${member.title}? This will close the session for this member.`);
    if (!confirmed) {
      return;
    }

    try {
      await request(`/api/members/${member.id}`, { method: "DELETE" });
      clearMemberRuntime(member.id);
      await refreshState();
    } catch (error) {
      showToast(error.message);
    }
  });
  actions.append(expandButton, removeButton);

  const head = document.createElement("div");
  head.className = "member-head";

  const avatarButton = document.createElement("button");
  avatarButton.className = "avatar-button";
  avatarButton.type = "button";
  avatarButton.title = "Change avatar";
  avatarButton.disabled = interactionLocked;
  avatarButton.addEventListener("click", () => openAvatarModal(member.id));

  const avatarImage = document.createElement("img");
  avatarImage.src = avatar?.asset_path ?? "";
  avatarImage.alt = avatar?.name ?? "Cat avatar";
  avatarButton.append(avatarImage);

  const meta = document.createElement("div");
  meta.className = "member-meta";

  const titleBlock = createMemberTitleBlock(member, {
    disabled: interactionLocked,
    scope: expanded ? "expanded" : "crew",
  });

  const subline = document.createElement("div");
  subline.className = "member-subline";

  const providerBadge = document.createElement("span");
  providerBadge.className = "member-provider";
  providerBadge.textContent = getProviderDisplayLabel(provider, member.provider);

  const statusBadge = document.createElement("span");
  statusBadge.className = "member-status";
  statusBadge.dataset.status = currentStatus;
  statusBadge.textContent = currentStatus;

  const skillsButton = document.createElement("button");
  skillsButton.className = "icon-chip";
  skillsButton.type = "button";
  skillsButton.textContent = "Skills";
  skillsButton.disabled = interactionLocked;
  skillsButton.addEventListener("click", () => openSkillModal(member));

  subline.append(providerBadge, statusBadge, skillsButton);
  meta.append(titleBlock, subline);
  head.append(avatarButton, meta);

  const chatLog = document.createElement("div");
  chatLog.className = "chat-log";
  chatLog.dataset.memberId = member.id;
  chatLog.dataset.scrollKey = `${expanded ? "expanded" : "crew"}:${member.id}`;

  if (member.messages.length === 0) {
    const emptyChat = document.createElement("div");
    emptyChat.className = "chat-empty";
    const strong = document.createElement("strong");
    strong.textContent = "Fresh paws";
    const text = document.createElement("p");
    text.textContent = "No messages yet. Say hello to wake up this member session.";
    emptyChat.append(strong, text);
    chatLog.append(emptyChat);
  } else {
    for (const message of member.messages) {
      chatLog.append(createMessageBubble(message));
    }
  }

  const composer = document.createElement("div");
  composer.className = "composer";

  ensureProviderModels(member.provider);

  const form = document.createElement("form");
  form.className = "composer-form";

  const textarea = document.createElement("textarea");
  textarea.dataset.interactionField = "composer";
  textarea.placeholder = `Message ${getProviderDisplayLabel(provider, member.provider)}`;
  textarea.rows = 2;
  textarea.disabled = interactionLocked;
  textarea.value = state.composerDrafts[member.id] ?? "";
  textarea.addEventListener("input", (event) => {
    state.composerDrafts[member.id] = event.target.value;
    syncSendButtonState(sendButton, member.id, event.target.value);
  });
  textarea.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  const sendButton = document.createElement("button");
  sendButton.className = "send-button";
  sendButton.type = "submit";
  sendButton.disabled = interactionLocked;
  syncSendButtonState(sendButton, member.id, textarea.value);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = textarea.value.trim();
    if (interactionLocked) {
      return;
    }

    if (pendingMembers.has(member.id)) {
      if (!text) {
        clearQueuedMessages(member.id);
        await cancelMemberStream(member.id);
        return;
      }
      enqueueMemberMessage(member.id, text);
      state.composerDrafts[member.id] = "";
      render();
      return;
    }

    if (!text) {
      return;
    }

    await startMemberStream(member.id, text);
  });

  form.append(textarea, sendButton);
  composer.append(form, createModelSelector(member, { disabled: interactionLocked }));

  article.append(actions, head, chatLog, composer);
  return article;
}

function createModelSelector(member, { disabled = false } = {}) {
  const wrap = document.createElement("label");
  wrap.className = "model-picker";

  const title = document.createElement("span");
  title.className = "model-picker__label";
  title.textContent = "Model";

  const select = document.createElement("select");
  select.className = "model-picker__select";
  select.disabled = disabled || providerModelLoads.has(member.provider);

  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = "Default";
  select.append(defaultOption);

  const models = state.providerModels[member.provider] ?? [];
  for (const model of models) {
    const option = document.createElement("option");
    option.value = model.id;
    option.textContent = model.label;
    select.append(option);
  }

  const selectedModel = member.session?.model_id ?? "";
  if (selectedModel && !models.some((model) => model.id === selectedModel)) {
    const unavailableOption = document.createElement("option");
    unavailableOption.value = selectedModel;
    unavailableOption.textContent = `${selectedModel} (Unavailable)`;
    select.append(unavailableOption);
  }

  select.value = selectedModel;
  select.addEventListener("change", async () => {
    const previousValue = member.session?.model_id ?? "";
    const nextValue = select.value || null;
    select.disabled = true;

    try {
      const payload = await request(`/api/members/${member.id}/model`, {
        method: "PATCH",
        body: { model_id: nextValue },
      });
      patchMember(payload.member);
      render();
    } catch (error) {
      select.value = previousValue;
      showToast(error.message);
      render();
    }
  });

  const hint = document.createElement("small");
  hint.className = "model-picker__hint";
  if (providerModelLoads.has(member.provider) && models.length === 0) {
    hint.textContent = "Loading available models...";
  } else if (selectedModel && !models.some((model) => model.id === selectedModel)) {
    hint.textContent = "The saved model is no longer in the current CLI list.";
  } else {
    hint.textContent = "Applies to future replies only.";
  }

  const dirLine = document.createElement("small");
  dirLine.className = "model-picker__dir";
  dirLine.textContent = `Dir: ${member.session?.working_dir ?? ""}`;

  wrap.append(title, select, hint, dirLine);
  return wrap;
}

function createMessageBubble(message) {
  const bubble = document.createElement("div");
  bubble.className = `message-bubble message-bubble--${message.role}`;
  if (message.error) {
    bubble.classList.add("message-bubble--error");
  }
  bubble.textContent = message.content;
  return bubble;
}

function createCrewNameBlock(crew) {
  const wrap = document.createElement("div");
  wrap.className = "name-row";

  if (state.editingCrewId === crew.id) {
    const form = document.createElement("form");
    form.className = "inline-name-form";

    const input = document.createElement("input");
    input.className = "inline-name-input inline-name-input--crew";
    input.type = "text";
    input.value = state.crewNameDraft;
    input.maxLength = 80;
    input.addEventListener("input", (event) => {
      state.crewNameDraft = event.target.value;
    });

    const saveButton = document.createElement("button");
    saveButton.className = "icon-chip icon-chip--soft";
    saveButton.type = "submit";
    saveButton.textContent = "Save";

    const cancelButton = document.createElement("button");
    cancelButton.className = "icon-chip";
    cancelButton.type = "button";
    cancelButton.textContent = "Cancel";
    cancelButton.addEventListener("click", cancelCrewRename);

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const payload = await request(`/api/crews/${crew.id}`, {
          method: "PATCH",
          body: { name: state.crewNameDraft },
        });
        patchCrew(payload.crew);
        cancelCrewRename(false);
        render();
      } catch (error) {
        showToast(error.message);
      }
    });

    form.append(input, saveButton, cancelButton);
    wrap.append(form);
    queueMicrotask(() => input.focus());
    return wrap;
  }

  const name = document.createElement("h2");
  name.className = "crew-name";
  name.textContent = crew.name;

  const editButton = document.createElement("button");
  editButton.className = "icon-chip";
  editButton.type = "button";
  editButton.textContent = "Edit name";
  editButton.addEventListener("click", () => startCrewRename(crew));

  wrap.append(name, editButton);
  return wrap;
}

function createMemberTitleBlock(member, { disabled = false, scope = "crew" } = {}) {
  const wrap = document.createElement("div");
  wrap.className = "name-row name-row--member";

  if (state.editingMemberId === member.id && state.editingMemberScope === scope) {
    const form = document.createElement("form");
    form.className = "inline-name-form inline-name-form--member";

    const input = document.createElement("input");
    input.className = "inline-name-input";
    input.type = "text";
    input.value = state.memberNameDraft;
    input.maxLength = 80;
    input.disabled = disabled;
    input.addEventListener("input", (event) => {
      state.memberNameDraft = event.target.value;
    });

    const saveButton = document.createElement("button");
    saveButton.className = "icon-chip icon-chip--soft";
    saveButton.type = "submit";
    saveButton.textContent = "Save";
    saveButton.disabled = disabled;

    const cancelButton = document.createElement("button");
    cancelButton.className = "icon-chip";
    cancelButton.type = "button";
    cancelButton.textContent = "Cancel";
    cancelButton.addEventListener("click", cancelMemberRename);

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const payload = await request(`/api/members/${member.id}`, {
          method: "PATCH",
          body: { title: state.memberNameDraft },
        });
        patchMember(payload.member);
        cancelMemberRename(false);
        render();
      } catch (error) {
        showToast(error.message);
      }
    });

    const actions = document.createElement("div");
    actions.className = "inline-name-actions";
    actions.append(saveButton, cancelButton);

    form.append(input, actions);
    wrap.append(form);
    queueMicrotask(() => input.focus());
    return wrap;
  }

  const title = document.createElement("button");
  title.className = "member-title member-title-button";
  title.type = "button";
  title.textContent = member.title;
  title.disabled = disabled;
  title.title = "Click to rename";
  title.setAttribute("aria-label", `Rename ${member.title}`);
  title.addEventListener("click", () => startMemberRename(member, scope));

  wrap.append(title);
  return wrap;
}

function renderProviderOptions() {
  providerOptions.replaceChildren();

  for (const provider of state.providers) {
    const button = document.createElement("button");
    button.className = "provider-option";
    button.type = "button";
    button.disabled = !provider.available || !state.activeCrewId;
    button.dataset.available = String(provider.available);
    button.dataset.selected = String(state.activeMemberProvider === provider.id);

    const name = document.createElement("strong");
    name.textContent = provider.label;

    const summary = document.createElement("span");
    summary.textContent = provider.summary;

    const statusLine = document.createElement("small");
    statusLine.textContent = provider.available ? "Available on this machine" : "CLI not detected";

    button.append(name, summary, statusLine);

    button.addEventListener("click", () => {
      if (!state.activeCrewId || !provider.available) {
        return;
      }
      state.activeMemberProvider = provider.id;
      renderProviderOptions();
    });

    providerOptions.append(button);
  }
}

function renderGlobalSettingsModal() {
  if (!themeOptions || !globalSkillSelected || !globalSkillOptions) {
    return;
  }

  themeOptions.replaceChildren();
  for (const theme of SITE_THEMES) {
    const button = document.createElement("button");
    button.className = "theme-option";
    button.type = "button";
    button.dataset.selected = String(state.globalSettingsThemeDraft === theme.id);

    const title = document.createElement("strong");
    title.textContent = theme.label;

    const description = document.createElement("small");
    description.textContent = theme.description;

    button.append(title, description);
    button.addEventListener("click", () => {
      state.globalSettingsThemeDraft = theme.id;
      renderGlobalSettingsModal();
    });
    themeOptions.append(button);
  }

  globalSkillSelected.replaceChildren();
  for (const skillRef of state.globalSkillSelections) {
    const row = document.createElement("div");
    row.className = "selected-skill-pill";

    const matched = findSkillByPath(skillRef, state.skills);
    const label = document.createElement("span");
    label.textContent = matched ? `${matched.name} — ${matched.path}` : skillRef;

    const removeButton = document.createElement("button");
    removeButton.className = "icon-chip icon-chip--danger";
    removeButton.type = "button";
    removeButton.textContent = "Remove";
    removeButton.addEventListener("click", () => {
      state.globalSkillSelections = state.globalSkillSelections.filter((item) => item !== skillRef);
      renderGlobalSettingsModal();
    });

    row.append(label, removeButton);
    globalSkillSelected.append(row);
  }

  renderSkillSuggestions({
    container: globalSkillOptions,
    skills: state.skills,
    query: state.globalSkillCustom,
    selectedPaths: state.globalSkillSelections,
    emptyLabel: "No matching system skills.",
    onSelect: (skillPath) => {
      state.globalSkillSelections = addUniqueSkillSelection(state.globalSkillSelections, skillPath);
      state.globalSkillCustom = "";
      globalSkillCustomInput.value = "";
      renderGlobalSettingsModal();
    },
  });
}

function renderCreateSkillOptions() {
  memberCreateSelected.replaceChildren();
  for (const skillRef of state.memberSkillSelections) {
    const row = document.createElement("div");
    row.className = "selected-skill-pill";

    const matched = findSkillByPath(skillRef, state.globalSkills);
    const label = document.createElement("span");
    label.textContent = matched ? `${matched.name} — ${matched.path}` : skillRef;

    const removeButton = document.createElement("button");
    removeButton.className = "icon-chip icon-chip--danger";
    removeButton.type = "button";
    removeButton.textContent = "Remove";
    removeButton.addEventListener("click", () => {
      state.memberSkillSelections = state.memberSkillSelections.filter((item) => item !== skillRef);
      renderCreateSkillOptions();
    });

    row.append(label, removeButton);
    memberCreateSelected.append(row);
  }

  renderSkillSuggestions({
    container: memberSkillOptions,
    skills: state.globalSkills,
    query: state.memberSkillCustom,
    selectedPaths: state.memberSkillSelections,
    emptyLabel: "No matching global skills.",
    onSelect: (skillPath) => {
      state.memberSkillSelections = addUniqueSkillSelection(state.memberSkillSelections, skillPath);
      state.memberSkillCustom = "";
      memberSkillCustomInput.value = "";
      renderCreateSkillOptions();
    },
  });
}

function renderSkillModal() {
  memberSkillSelected.replaceChildren();
  for (const skillRef of state.skillModalSelections) {
    const row = document.createElement("div");
    row.className = "selected-skill-pill";

    const matched = findSkillByPath(skillRef, state.globalSkills);
    const label = document.createElement("span");
    label.textContent = matched ? `${matched.name} — ${matched.path}` : skillRef;

    const removeButton = document.createElement("button");
    removeButton.className = "icon-chip icon-chip--danger";
    removeButton.type = "button";
    removeButton.textContent = "Remove";
    removeButton.addEventListener("click", () => {
      state.skillModalSelections = state.skillModalSelections.filter((item) => item !== skillRef);
      renderSkillModal();
    });

    row.append(label, removeButton);
    memberSkillSelected.append(row);
  }

  renderSkillSuggestions({
    container: skillModalOptions,
    skills: state.globalSkills,
    query: state.skillModalCustom,
    selectedPaths: state.skillModalSelections,
    emptyLabel: "No matching global skills.",
    onSelect: (skillPath) => {
      state.skillModalSelections = addUniqueSkillSelection(state.skillModalSelections, skillPath);
      state.skillModalCustom = "";
      skillModalCustomInput.value = "";
      renderSkillModal();
    },
  });
}

function renderSkillSuggestions({ container, skills, query, selectedPaths, emptyLabel, onSelect }) {
  container.replaceChildren();
  const suggestions = getSkillSuggestions(skills, query, selectedPaths);

  if (suggestions.length === 0) {
    const empty = document.createElement("div");
    empty.className = "skill-suggestion skill-suggestion--empty";
    empty.textContent = emptyLabel;
    container.append(empty);
    return;
  }

  for (const skill of suggestions) {
    const button = document.createElement("button");
    button.className = "skill-suggestion";
    button.type = "button";

    const textWrap = document.createElement("div");
    textWrap.className = "skill-suggestion__body";

    const title = document.createElement("strong");
    title.textContent = skill.name;

    const path = document.createElement("small");
    path.textContent = skill.path;

    textWrap.append(title, path);

    if (skill.description) {
      const description = document.createElement("small");
      description.textContent = skill.description;
      textWrap.append(description);
    }

    button.append(textWrap);
    button.addEventListener("click", () => onSelect(skill.path));
    container.append(button);
  }
}

function findSkillByPath(path, skills) {
  return (skills ?? []).find((skill) => skill.path === path) ?? null;
}

export function getSkillSuggestions(skills, query, selectedPaths, limit = 8) {
  const normalizedQuery = normalizeSkillQuery(query);
  const unselectedSkills = skills.filter((skill) => !selectedPaths.includes(skill.path));

  if (!normalizedQuery) {
    return unselectedSkills.slice(0, limit);
  }

  return unselectedSkills
    .map((skill) => ({
      skill,
      score: scoreSkillSuggestion(skill, normalizedQuery),
    }))
    .filter(({ score }) => score > 0)
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }
      return left.skill.name.localeCompare(right.skill.name);
    })
    .slice(0, limit)
    .map(({ skill }) => skill);
}

function normalizeSkillQuery(query) {
  return String(query ?? "").trim().toLowerCase();
}

function scoreSkillSuggestion(skill, normalizedQuery) {
  const name = normalizeSkillQuery(skill.name);
  const path = normalizeSkillQuery(skill.path);
  const description = normalizeSkillQuery(skill.description);

  if (name === normalizedQuery || path === normalizedQuery) {
    return 120;
  }
  if (name.startsWith(normalizedQuery)) {
    return 90;
  }
  if (path.startsWith(normalizedQuery)) {
    return 75;
  }
  if (name.includes(normalizedQuery)) {
    return 60;
  }
  if (description.includes(normalizedQuery)) {
    return 40;
  }
  if (path.includes(normalizedQuery)) {
    return 30;
  }
  return 0;
}

export function resolveSkillReference(reference, skills) {
  const trimmed = String(reference ?? "").trim();
  if (!trimmed) {
    return null;
  }

  const normalized = trimmed.toLowerCase();
  const exactPath = skills.find((skill) => skill.path.toLowerCase() === normalized);
  if (exactPath) {
    return exactPath.path;
  }

  const exactNameMatches = skills.filter((skill) => skill.name.toLowerCase() === normalized);
  if (exactNameMatches.length === 1) {
    return exactNameMatches[0].path;
  }

  const bestSuggestion = getSkillSuggestions(skills, trimmed, [], 1)[0];
  if (bestSuggestion) {
    const bestName = bestSuggestion.name.toLowerCase();
    if (bestName.startsWith(normalized) || bestSuggestion.path.toLowerCase() === normalized) {
      return bestSuggestion.path;
    }
  }

  return null;
}

function renderAvatarOptions() {
  avatarOptions.replaceChildren();

  for (const avatar of state.avatars) {
    const button = document.createElement("button");
    button.className = "avatar-option";
    button.type = "button";

    const image = document.createElement("img");
    image.src = avatar.asset_path;
    image.alt = avatar.name;

    const name = document.createElement("strong");
    name.textContent = avatar.name;

    const hint = document.createElement("small");
    hint.textContent = avatar.id;

    button.append(image, name, hint);
    button.addEventListener("click", async () => {
      if (!state.activeAvatarMemberId) {
        return;
      }

      try {
        const payload = await request(`/api/members/${state.activeAvatarMemberId}/avatar`, {
          method: "POST",
          body: { avatar_id: avatar.id },
        });
        patchMember(payload.member);
        closeAvatarModal();
        render();
      } catch (error) {
        showToast(error.message);
      }
    });

    avatarOptions.append(button);
  }
}

function injectOptimisticUserMessage(memberId, content) {
  const member = findMember(memberId);
  if (!member) {
    return;
  }

  member.messages = [
    ...member.messages,
    {
      id: `local-${Date.now()}`,
      role: "user",
      content,
      created_at: new Date().toISOString(),
      error: false,
    },
  ];
  member.status = "thinking";
}

function applyStreamDelta(memberId, mode, text) {
  const member = findMember(memberId);
  if (!member) {
    return;
  }

  const lastMessage = member.messages.at(-1);
  if (!lastMessage || lastMessage.role !== "assistant") {
    member.messages.push({
      id: `stream-${Date.now()}`,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      error: false,
    });
  }

  const target = member.messages.at(-1);
  if (mode === "replace") {
    target.content = text;
  } else {
    target.content += text;
  }
  target.error = false;
  member.status = "thinking";
}

function patchCrew(updatedCrew) {
  const index = state.crews.findIndex((crew) => crew.id === updatedCrew.id);
  if (index >= 0) {
    state.crews[index] = updatedCrew;
  }
}

function patchMember(updatedMember) {
  for (const crew of state.crews) {
    const memberIndex = crew.members.findIndex((member) => member.id === updatedMember.id);
    if (memberIndex >= 0) {
      crew.members[memberIndex] = updatedMember;
      return;
    }
  }
}

function findMember(memberId) {
  for (const crew of state.crews) {
    const member = crew.members.find((item) => item.id === memberId);
    if (member) {
      return member;
    }
  }
  return null;
}

function clearMemberRuntime(memberId) {
  const controller = memberStreams.get(memberId);
  if (controller) {
    controller.abort();
    memberStreams.delete(memberId);
  }

  pendingMembers.delete(memberId);

  if (state.activeAvatarMemberId === memberId) {
    closeAvatarModal();
  }

  if (state.activeSkillMemberId === memberId) {
    closeSkillModal();
  }

  if (state.activeExpandedMemberId === memberId) {
    closeExpandedMemberModal();
  }

  if (state.editingMemberId === memberId) {
    cancelMemberRename(false);
  }

  delete state.composerDrafts[memberId];
  clearQueuedMessages(memberId);
}

function clearCrewRuntime(crew) {
  if (state.activeCrewId === crew.id) {
    closeMemberModal();
  }

  if (state.editingCrewId === crew.id) {
    cancelCrewRename(false);
  }

  for (const member of crew.members) {
    clearMemberRuntime(member.id);
  }
}

function startCrewRename(crew) {
  state.editingCrewId = crew.id;
  state.crewNameDraft = crew.name;
  render();
}

function cancelCrewRename(shouldRender = true) {
  state.editingCrewId = null;
  state.crewNameDraft = "";
  if (shouldRender) {
    render();
  }
}

function startMemberRename(member, scope = "crew") {
  state.editingMemberId = member.id;
  state.editingMemberScope = scope;
  state.memberNameDraft = member.title;
  render();
}

function cancelMemberRename(shouldRender = true) {
  state.editingMemberId = null;
  state.editingMemberScope = null;
  state.memberNameDraft = "";
  if (shouldRender) {
    render();
  }
}

function openGlobalSettingsModal() {
  state.globalSettingsThemeDraft = state.siteTheme;
  state.globalSkillSelections = state.globalSkills.map((skill) => skill.path);
  state.globalSkillCustom = "";
  globalSkillCustomInput.value = "";
  globalSettingsModal.classList.remove("is-hidden");
  renderGlobalSettingsModal();
}

function closeGlobalSettingsModal() {
  state.globalSettingsThemeDraft = state.siteTheme;
  state.globalSkillSelections = [];
  state.globalSkillCustom = "";
  globalSkillCustomInput.value = "";
  globalSettingsModal.classList.add("is-hidden");
}

function openMemberModal(crewId) {
  state.activeCrewId = crewId;
  state.activeMemberProvider = "";
  state.memberTitleDraft = pickAvailableMemberName(getUsedMemberTitles(state.crews), Date.now(), state.memberNameCandidates);
  state.memberWorkingDirAuto = buildDefaultMemberWorkingDir(state.projectRoot, state.memberTitleDraft);
  state.memberWorkingDirDraft = state.memberWorkingDirAuto;
  state.memberWorkingDirTouched = false;
  state.memberSkillSelections = [];
  state.memberSkillCustom = "";
  memberTitleInput.value = state.memberTitleDraft;
  memberWorkingDirInput.value = state.memberWorkingDirDraft;
  memberSkillCustomInput.value = "";
  memberModal.classList.remove("is-hidden");
  renderProviderOptions();
  renderCreateSkillOptions();
}

function closeMemberModal() {
  state.activeCrewId = null;
  state.activeMemberProvider = "";
  state.memberTitleDraft = "";
  state.memberWorkingDirDraft = "";
  state.memberWorkingDirAuto = "";
  state.memberWorkingDirTouched = false;
  state.memberSkillSelections = [];
  state.memberSkillCustom = "";
  memberModal.classList.add("is-hidden");
}

function openSkillModal(member) {
  state.activeSkillMemberId = member.id;
  state.skillModalSelections = getMemberSkills(member).map((skill) => skill.path);
  state.skillModalCustom = "";
  skillModalCustomInput.value = "";
  skillModal.classList.remove("is-hidden");
  renderSkillModal();
}

function closeSkillModal() {
  state.activeSkillMemberId = null;
  state.skillModalSelections = [];
  state.skillModalCustom = "";
  skillModal.classList.add("is-hidden");
}

function addCreateSkillSelection(reference) {
  if (!reference) {
    showToast("Choose a skill from the global skill list.");
    return;
  }
  state.memberSkillSelections = addUniqueSkillSelection(state.memberSkillSelections, reference);
  state.memberSkillCustom = "";
  memberSkillCustomInput.value = "";
  renderCreateSkillOptions();
}

function addSkillModalSelection(reference) {
  if (!reference) {
    showToast("Choose a skill from the global skill list.");
    return;
  }
  state.skillModalSelections = addUniqueSkillSelection(state.skillModalSelections, reference);
  state.skillModalCustom = "";
  skillModalCustomInput.value = "";
  renderSkillModal();
}

function addGlobalSkillSelection(reference) {
  if (!reference) {
    showToast("Choose a discovered system skill.");
    return;
  }
  state.globalSkillSelections = addUniqueSkillSelection(state.globalSkillSelections, reference);
  state.globalSkillCustom = "";
  globalSkillCustomInput.value = "";
  renderGlobalSettingsModal();
}

function addUniqueSkillSelection(selections, reference) {
  return selections.includes(reference) ? selections : [...selections, reference];
}

function getMemberSkills(member) {
  if (Array.isArray(member.session?.skills) && member.session.skills.length > 0) {
    return member.session.skills;
  }
  if (member.session?.skill_name && member.session?.skill_path) {
    return [{ name: member.session.skill_name, path: member.session.skill_path }];
  }
  return [];
}

function openAvatarModal(memberId) {
  state.activeAvatarMemberId = memberId;
  avatarModal.classList.remove("is-hidden");
}

function closeAvatarModal() {
  state.activeAvatarMemberId = null;
  avatarModal.classList.add("is-hidden");
}

function openExpandedMemberModal(memberId) {
  state.activeExpandedMemberId = memberId;
  expandedMemberModal.classList.remove("is-hidden");
  renderExpandedMemberModal();
}

function closeExpandedMemberModal() {
  if (state.editingMemberScope === "expanded") {
    cancelMemberRename(false);
  }
  state.activeExpandedMemberId = null;
  expandedMemberModal.classList.add("is-hidden");
  expandedMemberContent.replaceChildren();
}

function renderExpandedMemberModal() {
  expandedMemberContent.replaceChildren();

  if (!state.activeExpandedMemberId) {
    expandedMemberModal.classList.add("is-hidden");
    return;
  }

  const member = findMember(state.activeExpandedMemberId);
  if (!member) {
    closeExpandedMemberModal();
    return;
  }

  expandedMemberModal.classList.remove("is-hidden");
  expandedMemberContent.append(createMemberElement(member, { expanded: true }));
}

function getProviderDisplayLabel(provider, providerId) {
  if (providerId === "github_copilot") {
    return "Copilot";
  }
  return provider?.label ?? providerId;
}

function locateChatScrollTarget(key) {
  return document.querySelector(`[data-scroll-key="${key}"]`);
}

function locateMemberInteractionTarget(snapshot) {
  if (!snapshot?.memberId || !snapshot?.field) {
    return null;
  }

  const root = snapshot.scope === "expanded" ? expandedMemberContent : crewList;
  if (!root?.querySelector) {
    return null;
  }

  return root.querySelector(
    `[data-member-id="${snapshot.memberId}"] [data-interaction-field="${snapshot.field}"]`,
  );
}

export function captureMemberInteractionState(activeElement) {
  if (!activeElement?.closest) {
    return null;
  }

  const memberCard = activeElement.closest("[data-member-id]");
  if (!memberCard?.dataset?.memberId) {
    return null;
  }

  const field = activeElement.dataset?.interactionField;
  if (!field) {
    return null;
  }

  const scope = activeElement.closest("#expanded-member-content") ? "expanded" : "crew";
  return {
    memberId: memberCard.dataset.memberId,
    field,
    value: typeof activeElement.value === "string" ? activeElement.value : "",
    selectionStart: typeof activeElement.selectionStart === "number" ? activeElement.selectionStart : null,
    selectionEnd: typeof activeElement.selectionEnd === "number" ? activeElement.selectionEnd : null,
    scope,
  };
}

export function captureChatScrollState(chatLogs) {
  const snapshot = {};
  for (const chatLog of chatLogs ?? []) {
    const key = chatLog?.dataset?.scrollKey ?? chatLog?.dataset?.memberId;
    if (!key || typeof chatLog.scrollTop !== "number") {
      continue;
    }
    snapshot[key] = chatLog.scrollTop;
  }
  return snapshot;
}

export function restoreChatScrollState(snapshot, resolver) {
  if (!snapshot || typeof resolver !== "function") {
    return false;
  }

  for (const [key, scrollTop] of Object.entries(snapshot)) {
    const target = resolver(key);
    if (!target || typeof scrollTop !== "number") {
      continue;
    }
    target.scrollTop = scrollTop;
  }
  return true;
}

export function restoreMemberInteractionState(snapshot, resolver) {
  if (!snapshot || typeof resolver !== "function") {
    return false;
  }

  const target = resolver(snapshot);
  if (!target || target.disabled) {
    return false;
  }

  if (typeof snapshot.value === "string" && "value" in target) {
    target.value = snapshot.value;
  }
  if (typeof target.focus === "function") {
    target.focus();
  }
  if (
    typeof snapshot.selectionStart === "number"
    && typeof snapshot.selectionEnd === "number"
    && typeof target.setSelectionRange === "function"
  ) {
    target.setSelectionRange(snapshot.selectionStart, snapshot.selectionEnd);
  }
  return true;
}

function getQueuedMessages(memberId) {
  return state.memberQueues[memberId] ?? [];
}

function getQueuedMessageCount(memberId) {
  return getQueuedMessages(memberId).length;
}

function enqueueMemberMessage(memberId, message) {
  state.memberQueues[memberId] = [...getQueuedMessages(memberId), message];
}

function dequeueMemberMessage(memberId) {
  const queue = getQueuedMessages(memberId);
  if (queue.length === 0) {
    return null;
  }
  const [next, ...rest] = queue;
  if (rest.length === 0) {
    delete state.memberQueues[memberId];
  } else {
    state.memberQueues[memberId] = rest;
  }
  return next;
}

function clearQueuedMessages(memberId) {
  delete state.memberQueues[memberId];
}

export function getSendActionState({ isPending, draftText, queueLength }) {
  const trimmedDraft = draftText.trim();
  if (!isPending) {
    return { mode: "send", label: "Send" };
  }
  if (!trimmedDraft) {
    return { mode: "cancel", label: "Cancel" };
  }
  return {
    mode: "queue",
    label: queueLength > 1 ? `Queue (${queueLength})` : "Queue",
  };
}

function syncSendButtonState(button, memberId, draftText) {
  const action = getSendActionState({
    isPending: pendingMembers.has(memberId),
    draftText,
    queueLength: getQueuedMessageCount(memberId) + (draftText.trim() ? 1 : 0),
  });
  button.textContent = action.label;
  button.dataset.actionMode = action.mode;
}

async function cancelMemberStream(memberId) {
  const controller = memberStreams.get(memberId);
  if (controller) {
    controller.abort();
  }

  try {
    const payload = await request(`/api/members/${memberId}/cancel`, { method: "POST" });
    if (payload?.member) {
      patchMember(payload.member);
    }
  } catch (error) {
    showToast(error.message);
  } finally {
    render();
  }
}

async function startMemberStream(memberId, text) {
  state.composerDrafts[memberId] = "";
  pendingMembers.add(memberId);
  const controller = new AbortController();
  memberStreams.set(memberId, controller);
  render();

  try {
    await streamJsonLines(`/api/members/${memberId}/messages/stream`, {
      method: "POST",
      body: { content: text },
      signal: controller.signal,
    }, (payload) => {
      if (payload.type === "member" && payload.member) {
        patchMember(payload.member);
        render();
        return;
      }

      if (payload.type === "delta") {
        applyStreamDelta(payload.memberId, payload.mode, payload.text);
        render();
        return;
      }

      if (payload.type === "done" && payload.member) {
        patchMember(payload.member);
        render();
        return;
      }

      if (payload.type === "error") {
        if (payload.member) {
          patchMember(payload.member);
        }
        if (payload.message) {
          showToast(payload.message);
        }
        render();
      }
    });
  } catch (error) {
    if (error.name !== "AbortError") {
      showToast(error.message);
    }
  } finally {
    pendingMembers.delete(memberId);
    memberStreams.delete(memberId);
    render();

    const nextMessage = dequeueMemberMessage(memberId);
    if (nextMessage) {
      await startMemberStream(memberId, nextMessage);
    }
  }
}

function providerMap() {
  return new Map(state.providers.map((provider) => [provider.id, provider]));
}

function avatarMap() {
  return new Map(state.avatars.map((avatar) => [avatar.id, avatar]));
}

function ensureProviderModels(providerId, { force = false } = {}) {
  const cachedModels = state.providerModels[providerId];
  const fetchedAt = state.providerModelsFetchedAt[providerId] ?? 0;
  const isFresh = Date.now() - fetchedAt < 60_000;

  if (!force && cachedModels && isFresh) {
    return;
  }

  if (providerModelLoads.has(providerId)) {
    return;
  }

  const load = request(`/api/providers/${providerId}/models`)
    .then((payload) => {
      state.providerModels[providerId] = payload.models ?? [];
      state.providerModelsFetchedAt[providerId] = Date.now();
      render();
    })
    .catch((error) => {
      showToast(error.message);
    })
    .finally(() => {
      providerModelLoads.delete(providerId);
      render();
    });

  providerModelLoads.set(providerId, load);
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 2600);
}

async function request(url, options = {}) {
  const finalOptions = { ...options, headers: { ...(options.headers ?? {}) } };

  if (finalOptions.body && typeof finalOptions.body !== "string") {
    finalOptions.headers["Content-Type"] = "application/json";
    finalOptions.body = JSON.stringify(finalOptions.body);
  }

  const response = await fetch(url, finalOptions);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // ignore malformed error bodies
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

async function streamJsonLines(url, options = {}, onEvent) {
  const finalOptions = { ...options, headers: { ...(options.headers ?? {}) } };

  if (finalOptions.body && typeof finalOptions.body !== "string") {
    finalOptions.headers["Content-Type"] = "application/json";
    finalOptions.body = JSON.stringify(finalOptions.body);
  }

  const response = await fetch(url, finalOptions);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // ignore malformed error bodies
    }
    throw new Error(detail);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Streaming is not available in this browser.");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

    let boundary = buffer.indexOf("\n");
    while (boundary >= 0) {
      const line = buffer.slice(0, boundary).trim();
      buffer = buffer.slice(boundary + 1);
      if (line) {
        onEvent(JSON.parse(line));
      }
      boundary = buffer.indexOf("\n");
    }

    if (done) {
      break;
    }
  }

  if (buffer.trim()) {
    onEvent(JSON.parse(buffer.trim()));
  }
}
