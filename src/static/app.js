const list = document.getElementById("task-list");
const form = document.getElementById("task-form");
const errorBox = document.getElementById("error");
const emptyBox = document.getElementById("empty");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

function renderTask(task) {
  const item = document.createElement("li");
  item.className = `task ${task.priority}${task.done ? " done" : ""}`;

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = task.done;
  checkbox.addEventListener("change", async () => {
    await api(`/api/tasks/${task.id}`, {
      method: "PATCH",
      body: JSON.stringify({ done: checkbox.checked }),
    });
    refresh();
  });

  const info = document.createElement("div");
  info.className = "info";
  const title = document.createElement("div");
  title.className = "title";
  title.textContent = task.title;
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = [
    task.course || "No course",
    `Priority: ${task.priority}`,
    task.due_date ? `Due: ${task.due_date}` : "No due date",
  ].join("  |  ");
  info.append(title, meta);

  const remove = document.createElement("button");
  remove.className = "delete";
  remove.textContent = "Delete";
  remove.addEventListener("click", async () => {
    await api(`/api/tasks/${task.id}`, { method: "DELETE" });
    refresh();
  });

  item.append(checkbox, info, remove);
  return item;
}

async function refresh() {
  const [tasks, stats] = await Promise.all([api("/api/tasks"), api("/api/stats")]);
  list.replaceChildren(...tasks.map(renderTask));
  emptyBox.hidden = tasks.length > 0;
  document.getElementById("stat-total").textContent = stats.total;
  document.getElementById("stat-pending").textContent = stats.pending;
  document.getElementById("stat-done").textContent = stats.done;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");
  try {
    await api("/api/tasks", {
      method: "POST",
      body: JSON.stringify({
        title: document.getElementById("title").value,
        course: document.getElementById("course").value,
        priority: document.getElementById("priority").value,
        due_date: document.getElementById("due_date").value || null,
      }),
    });
    form.reset();
    refresh();
  } catch (err) {
    showError(err.message);
  }
});

refresh().catch((err) => showError(err.message));
