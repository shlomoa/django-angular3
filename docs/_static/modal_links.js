(function () {
    "use strict";

    const links = document.querySelectorAll("a.modal-link");
    if (links.length === 0) {
        return;
    }

    const dialog = document.createElement("dialog");
    dialog.id = "sphinx-modal";
    dialog.setAttribute("aria-labelledby", "sphinx-modal-title");
    dialog.innerHTML = `
        <header id="sphinx-modal-header">
            <h2 id="sphinx-modal-title">Referenced documentation</h2>
            <button id="sphinx-modal-close" type="button" autofocus
                    aria-label="Close referenced documentation">&times;</button>
        </header>
        <div id="sphinx-modal-body" aria-live="polite"></div>
    `;
    document.body.appendChild(dialog);

    const modalBody = dialog.querySelector("#sphinx-modal-body");
    const closeButton = dialog.querySelector("#sphinx-modal-close");
    let activeRequest;

    closeButton.addEventListener("click", function () {
        dialog.close();
    });

    dialog.addEventListener("close", function () {
        activeRequest?.abort();
    });

    links.forEach(function (link) {
        link.addEventListener("click", async function (event) {
            event.preventDefault();
            activeRequest?.abort();
            activeRequest = new AbortController();

            modalBody.textContent = "Loading and rendering content from GitHub...";
            if (!dialog.open) {
                dialog.showModal();
            }

            try {
                const target = parseGitHubBlobUrl(link.href);
                const markdown = await fetchText(target.rawUrl, activeRequest.signal);
                const html = await renderMarkdown(
                    markdown,
                    target.repository,
                    activeRequest.signal,
                );
                modalBody.innerHTML = html;
                assignHeadingIds();
                scrollToFragment(target.fragment);
            } catch (error) {
                if (error.name !== "AbortError") {
                    showError(error, link.href);
                }
            }
        });
    });

    function parseGitHubBlobUrl(href) {
        const url = new URL(href);
        const segments = url.pathname.split("/").filter(Boolean);

        if (url.hostname.toLowerCase() !== "github.com" ||
            segments.length < 5 || segments[2] !== "blob") {
            throw new Error("The modal link must target a GitHub file URL.");
        }

        const [owner, repository, , revision, ...path] = segments;
        const encodedPath = [owner, repository, revision, ...path]
            .map(encodeURIComponent)
            .join("/");

        return {
            fragment: decodeURIComponent(url.hash.slice(1)),
            rawUrl: `https://raw.githubusercontent.com/${encodedPath}`,
            repository: `${owner}/${repository}`,
        };
    }

    async function fetchText(url, signal) {
        const response = await fetch(url, {signal});
        if (!response.ok) {
            throw new Error(`Could not load the linked file (status ${response.status}).`);
        }
        return response.text();
    }

    async function renderMarkdown(markdown, repository, signal) {
        const response = await fetch("https://api.github.com/markdown", {
            method: "POST",
            headers: {
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            body: JSON.stringify({
                text: markdown,
                mode: "gfm",
                context: repository,
            }),
            signal,
        });
        if (!response.ok) {
            throw new Error(`Could not render the linked file (status ${response.status}).`);
        }
        return response.text();
    }

    function assignHeadingIds() {
        const slugCounts = new Map();

        modalBody.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach(function (heading) {
            const baseSlug = heading.textContent
                .trim()
                .toLowerCase()
                .replace(/[^a-z0-9\s-]/g, "")
                .replace(/\s+/g, "-");
            const count = slugCounts.get(baseSlug) || 0;
            slugCounts.set(baseSlug, count + 1);
            heading.id = count === 0 ? baseSlug : `${baseSlug}-${count}`;
        });
    }

    function scrollToFragment(fragment) {
        if (!fragment) {
            modalBody.scrollTop = 0;
            return;
        }

        const target = Array.from(modalBody.querySelectorAll("[id]")).find(function (element) {
            return element.id === fragment || element.id === `user-content-${fragment}`;
        });
        target?.scrollIntoView({block: "start"});
    }

    function showError(error, href) {
        modalBody.replaceChildren();

        const message = document.createElement("p");
        message.textContent = error.message || "Could not open the linked documentation.";

        const fallback = document.createElement("a");
        fallback.href = href;
        fallback.target = "_blank";
        fallback.rel = "noopener noreferrer";
        fallback.textContent = "Open the documentation in a new tab";

        modalBody.append(message, fallback);
    }
}());
