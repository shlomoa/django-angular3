import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const MODAL_SCRIPT = new URL("../docs/_static/modal_links.js", import.meta.url);
const TARGET_URL = "https://github.com/shlomoa/django-angular3/blob/main/doc/specifications/SPECIFICATIONS.md#21-configuration-and-input-categories";

class FakeElement {
    constructor(tagName = "div") {
        this.tagName = tagName.toUpperCase();
        this.children = [];
        this.listeners = new Map();
        this.open = false;
        this.id = "";
        this.textContent = "";
        this.scrollTop = 0;
    }

    addEventListener(type, listener) {
        this.listeners.set(type, listener);
    }

    append(...children) {
        this.children.push(...children);
    }

    appendChild(child) {
        this.children.push(child);
        return child;
    }

    close() {
        this.open = false;
        this.listeners.get("close")?.();
    }

    querySelector(selector) {
        if (selector === "#sphinx-modal-body") return this.modalBody;
        if (selector === "#sphinx-modal-close") return this.closeButton;
        return null;
    }

    querySelectorAll(selector) {
        if (selector === "h1, h2, h3, h4, h5, h6" || selector === "[id]") {
            return this.headings ?? [];
        }
        return [];
    }

    replaceChildren(...children) {
        this.children = children;
    }

    setAttribute(name, value) {
        this[name] = value;
    }

    set innerHTML(value) {
        this._innerHTML = value;
        if (this.tagName === "DIALOG") {
            this.modalBody = new FakeElement();
            this.closeButton = new FakeElement("button");
        } else if (value.includes("2.1. Configuration and input categories")) {
            const heading = new FakeElement("h3");
            heading.textContent = "2.1. Configuration and input categories";
            heading.scrollIntoView = options => {
                heading.scrollOptions = options;
            };
            this.headings = [heading];
        }
    }

    get innerHTML() {
        return this._innerHTML;
    }

    showModal() {
        this.open = true;
    }
}

function createHarness() {
    const link = new FakeElement("a");
    link.href = TARGET_URL;
    const body = new FakeElement("body");
    const fetchCalls = [];

    const document = {
        body,
        createElement: tagName => new FakeElement(tagName),
        querySelectorAll: selector => selector === "a.modal-link" ? [link] : [],
    };

    const fetch = async (url, options = {}) => {
        fetchCalls.push({url, options});
        if (url === "https://api.github.com/markdown") {
            return {
                ok: true,
                text: async () => "<h3>2.1. Configuration and input categories</h3>",
            };
        }
        return {ok: true, text: async () => "### 2.1. Configuration and input categories"};
    };

    return {body, document, fetch, fetchCalls, link};
}

test("modal link loads GitHub Markdown and scrolls to its fragment", async () => {
    const harness = createHarness();
    const source = await readFile(MODAL_SCRIPT, "utf8");
    vm.runInNewContext(source, {
        AbortController,
        Array,
        console,
        decodeURIComponent,
        document: harness.document,
        fetch: harness.fetch,
        JSON,
        Map,
        URL,
    });

    let defaultPrevented = false;
    await harness.link.listeners.get("click")({
        preventDefault() {
            defaultPrevented = true;
        },
    });

    const dialog = harness.body.children[0];
    const heading = dialog.modalBody.headings[0];
    assert.equal(defaultPrevented, true);
    assert.equal(dialog.open, true);
    assert.equal(
        harness.fetchCalls[0].url,
        "https://raw.githubusercontent.com/shlomoa/django-angular3/main/doc/specifications/SPECIFICATIONS.md",
    );
    assert.equal(harness.fetchCalls[1].url, "https://api.github.com/markdown");
    assert.deepEqual(JSON.parse(harness.fetchCalls[1].options.body), {
        text: "### 2.1. Configuration and input categories",
        mode: "gfm",
        context: "shlomoa/django-angular3",
    });
    assert.equal(heading.id, "21-configuration-and-input-categories");
    assert.equal(heading.scrollOptions.block, "start");

    dialog.closeButton.listeners.get("click")();
    assert.equal(dialog.open, false);
    assert.equal(harness.fetchCalls[1].options.signal.aborted, true);
});
