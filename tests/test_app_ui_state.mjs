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
  captureMemberInteractionState,
  captureChatScrollState,
  getSendActionState,
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
