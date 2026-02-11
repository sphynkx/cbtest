const DEFAULT_THREAD_ID = "thread::demo";

async function apiGet(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of children) {
    if (typeof c === "string") node.appendChild(document.createTextNode(c));
    else if (c) node.appendChild(c);
  }
  return node;
}

function renderReplyForm({ parentId, onDone }) {
  const author = el("input", { class: "input", placeholder: "Author Name" });
  const text = el("textarea", { class: "textarea", placeholder: "Reply text" });

  const sendBtn = el("button", {
    class: "btn",
    onclick: async () => {
      const a = author.value.trim();
      const t = text.value.trim();
      if (!a || !t) return alert("Fill Author and Text fields");
      await apiPost("/api/comments", {
        thread_id: DEFAULT_THREAD_ID,
        parent_id: parentId,
        author: a,
        text: t,
      });
      onDone();
    }
  }, ["Send"]);

  const cancelBtn = el("button", { class: "btn btn-secondary" }, ["Cancel"]);

  const form = el("div", { class: "reply-form" }, [
    el("div", { class: "form-row" }, [author]),
    el("div", { class: "form-row" }, [text]),
    el("div", { class: "form-row form-row-inline" }, [sendBtn, cancelBtn]),
  ]);

  cancelBtn.addEventListener("click", () => form.remove());
  return form;
}

function renderComment(node, level = 0, onReload) {
  const header = el("div", { class: "comment-header" }, [
    el("span", { class: "comment-author" }, [node.author]),
    el("span", { class: "comment-date" }, [new Date(node.created_at).toLocaleString()]),
  ]);

  const body = el("div", { class: "comment-body" }, [node.text]);

  const actions = el("div", { class: "comment-actions" });
  const replyBtn = el("button", { class: "btn btn-small btn-secondary" }, ["Reply"]);

  replyBtn.addEventListener("click", () => {
    if (actions.querySelector(".reply-form")) return;
    actions.appendChild(renderReplyForm({ parentId: node.id, onDone: onReload }));
  });

  actions.appendChild(replyBtn);

  const wrap = el("div", { class: "comment", style: `margin-left:${level * 18}px` }, [
    header, body, actions
  ]);

  const childrenWrap = el("div", { class: "comment-children" });
  for (const ch of (node.children || [])) {
    childrenWrap.appendChild(renderComment(ch, level + 1, onReload));
  }
  wrap.appendChild(childrenWrap);

  return wrap;
}

async function loadAndRender() {
  const root = document.getElementById("comments");
  root.innerHTML = "Loading..";
  const tree = await apiGet(`/api/comments/tree?thread_id=${encodeURIComponent(DEFAULT_THREAD_ID)}`);
  root.innerHTML = "";
  if (!tree.length) {
    root.appendChild(el("div", { class: "muted" }, ["No comments yet."]));
    return;
  }
  for (const n of tree) root.appendChild(renderComment(n, 0, loadAndRender));
}

document.getElementById("sendRoot").addEventListener("click", async () => {
  const author = document.getElementById("rootAuthor").value.trim();
  const text = document.getElementById("rootText").value.trim();
  if (!author || !text) return alert("Fill Author and Text fields");

  await apiPost("/api/comments", {
    thread_id: DEFAULT_THREAD_ID,
    parent_id: null,
    author,
    text,
  });

  document.getElementById("rootText").value = "";
  await loadAndRender();
});

document.getElementById("reload").addEventListener("click", loadAndRender);

loadAndRender().catch(err => {
  console.error(err);
  alert("Error. Check if BE is running and /api/health responsing.");
});