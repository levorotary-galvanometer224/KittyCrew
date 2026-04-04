import test from "node:test";
import assert from "node:assert/strict";

function createStubElement() {
  return {
    value: "",
    disabled: false,
    dataset: {},
    classList: { add() {}, remove() {} },
    addEventListener() {},
    append() {},
    appendChild() {},
    replaceChildren() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
    closest() { return null; },
    focus() {},
    setAttribute() {},
  };
}

globalThis.window = {
  setTimeout,
  clearTimeout,
};

globalThis.fetch = async () => {
  throw new Error("fetch should not be called in unit tests");
};

globalThis.document = {
  activeElement: null,
  addEventListener() {},
  querySelector() {
    return createStubElement();
  },
  querySelectorAll() {
    return [];
  },
};

const {
  buildDefaultMemberWorkingDir,
  captureMemberInteractionState,
  captureChatScrollState,
  getSendActionState,
  getSkillSuggestions,
  isMemberInteractionLocked,
  pickAvailableMemberName,
  resolveSkillReference,
  restoreMemberInteractionState,
  restoreChatScrollState,
} = await import("../src/kittycrew/static/app.js");

test("captures and restores member composer interaction state", () => {
  const card = {
    dataset: { memberId: "member-1" },
    closest(selector) {
      if (selector === "#expanded-member-content") {
        return null;
      }
      if (selector === "#crew-list") {
        return {};
      }
      return null;
    },
  };

  const activeInput = {
    dataset: { interactionField: "composer" },
    value: "draft reply",
    selectionStart: 3,
    selectionEnd: 8,
    closest(selector) {
      if (selector === "[data-member-id]") {
        return card;
      }
      return null;
    },
  };

  const snapshot = captureMemberInteractionState(activeInput);
  assert.deepEqual(snapshot, {
    memberId: "member-1",
    field: "composer",
    value: "draft reply",
    selectionStart: 3,
    selectionEnd: 8,
    scope: "crew",
  });

  let focused = false;
  let restoredSelection = null;
  const replacementInput = {
    disabled: false,
    value: "",
    focus() {
      focused = true;
    },
    setSelectionRange(start, end) {
      restoredSelection = [start, end];
    },
  };

  const restored = restoreMemberInteractionState(snapshot, () => replacementInput);
  assert.equal(restored, true);
  assert.equal(focused, true);
  assert.equal(replacementInput.value, "draft reply");
  assert.deepEqual(restoredSelection, [3, 8]);
});

test("chooses cancel or queue send action while a member is thinking", () => {
  assert.deepEqual(getSendActionState({ isPending: false, draftText: "hello", queueLength: 0 }), {
    mode: "send",
    label: "Send",
  });
  assert.deepEqual(getSendActionState({ isPending: true, draftText: "", queueLength: 0 }), {
    mode: "cancel",
    label: "Cancel",
  });
  assert.deepEqual(getSendActionState({ isPending: true, draftText: "next task", queueLength: 0 }), {
    mode: "queue",
    label: "Queue",
  });
  assert.deepEqual(getSendActionState({ isPending: true, draftText: "next task", queueLength: 2 }), {
    mode: "queue",
    label: "Queue (2)",
  });
});

test("preserves chat scroll positions without snapping to bottom", () => {
  const chatLog = {
    dataset: { memberId: "member-1" },
    scrollTop: 120,
  };

  const snapshot = captureChatScrollState([chatLog]);
  assert.deepEqual(snapshot, { "member-1": 120 });

  let restored = null;
  const replacementLog = {
    scrollTop: 0,
  };

  restoreChatScrollState(snapshot, (memberId) => {
    restored = memberId;
    return replacementLog;
  });

  assert.equal(restored, "member-1");
  assert.equal(replacementLog.scrollTop, 120);
});

test("ranks skill suggestions by name and excludes selected skills", () => {
  const skills = [
    { name: "frontend-design", path: "/skills/frontend-design/SKILL.md", description: "UI polish" },
    { name: "brainstorming", path: "/skills/brainstorming/SKILL.md", description: "Design first" },
    { name: "frontend-debug", path: "/skills/frontend-debug/SKILL.md", description: "Fix UI bugs" },
  ];

  const suggestions = getSkillSuggestions(skills, "front", ["/skills/frontend-debug/SKILL.md"]);
  assert.deepEqual(
    suggestions.map((skill) => skill.path),
    ["/skills/frontend-design/SKILL.md"],
  );
});

test("resolves typed skill names to canonical paths when unambiguous", () => {
  const skills = [
    { name: "frontend-design", path: "/skills/frontend-design/SKILL.md", description: "UI polish" },
    { name: "brainstorming", path: "/skills/brainstorming/SKILL.md", description: "Design first" },
  ];

  assert.equal(
    resolveSkillReference("frontend-design", skills),
    "/skills/frontend-design/SKILL.md",
  );
  assert.equal(
    resolveSkillReference("/skills/brainstorming/SKILL.md", skills),
    "/skills/brainstorming/SKILL.md",
  );
  assert.equal(resolveSkillReference("custom-skill", skills), null);
});

test("returns null for empty or unknown skill references", () => {
  const skills = [{ name: "brainstorming", path: "/skills/brainstorming/SKILL.md", description: "Design first" }];

  assert.equal(resolveSkillReference("", skills), null);
  assert.equal(resolveSkillReference("missing-skill", skills), null);
});

test("keeps expanded member detail interactive while the strip card stays locked", () => {
  assert.equal(
    isMemberInteractionLocked({ activeExpandedMemberId: "member-1", editingMemberScope: "expanded" }, "member-1", true),
    false,
  );
  assert.equal(
    isMemberInteractionLocked({ activeExpandedMemberId: "member-1", editingMemberScope: "expanded" }, "member-1", false),
    false,
  );
});

test("builds create-member default working directory from the project root and title", () => {
  assert.equal(
    buildDefaultMemberWorkingDir("/Users/kc/Desktop/个人资料/个人项目/KittyCrew", "Mochi Whiskers"),
    "/tmp/KittyCrew/Mochi-Whiskers",
  );
});

test("picks an unused cat-themed member name", () => {
  const name = pickAvailableMemberName(["Mochi Whiskers", "Poppy Paws"], 0);
  assert.notEqual(name, "Mochi Whiskers");
  assert.notEqual(name, "Poppy Paws");
  assert.equal(typeof name, "string");
  assert.ok(name.length > 0);
});
