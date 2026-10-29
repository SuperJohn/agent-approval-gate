(function () {
  function load() {
    if (location.protocol !== "file:") {
      return fetch("data/runs.json")
        .then(function (res) {
          if (!res.ok) throw new Error("status");
          return res.json();
        })
        .catch(function () {
          return window.HL_RUNS || null;
        });
    }
    return Promise.resolve(window.HL_RUNS || null);
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function pretty(value) {
    return JSON.stringify(value, null, 2);
  }

  var data = null;
  var current = null;
  var phase = "pending";
  var clockJumped = false;
  var showEdit = false;

  function selectedId() {
    var hash = location.hash.replace("#", "");
    if (hash && data.runs.some(function (run) { return run.id === hash; })) return hash;
    return data.runs[0].id;
  }

  function continuation() {
    if (phase === "pending") return null;
    if (clockJumped) return current.continuations.late;
    return current.continuations[phase];
  }

  function render() {
    renderList();
    renderTimeline();
    renderAudit();
    renderCard();
    document.body.dataset.ready = "true";
    document.body.dataset.phase = clockJumped && phase !== "pending" ? "late" : phase;
  }

  function renderList() {
    var nav = document.getElementById("run-list");
    nav.replaceChildren();
    data.runs.forEach(function (run) {
      var button = el("button", "run");
      button.type = "button";
      button.dataset.run = run.id;
      button.setAttribute("aria-pressed", run.id === current.id ? "true" : "false");
      button.append(el("strong", null, run.title));
      button.append(el("span", null, run.lesson));
      button.addEventListener("click", function () {
        location.hash = run.id;
        select(run.id);
      });
      nav.append(button);
    });
  }

  function steps() {
    var items = current.steps_before.slice();
    var branch = continuation();
    if (branch) items = items.concat(branch.steps);
    return items;
  }

  function renderTimeline() {
    document.getElementById("lesson").textContent = current.lesson;
    var list = document.getElementById("timeline");
    list.replaceChildren();
    steps().forEach(function (step) {
      var item = el("li", "step " + step.kind);
      item.dataset.event = step.event;
      item.append(el("span", "dot"));
      var body = el("div");
      body.append(el("h3", null, step.title));
      if (step.body) body.append(el("p", null, step.body));
      if (step.at) body.append(el("span", "when", step.at));
      if (step.code) {
        var pre = el("pre");
        pre.textContent = step.code;
        if (step.collapse) {
          var details = el("details");
          details.append(el("summary", null, "Full serialized state"));
          details.append(pre);
          body.append(details);
        } else {
          body.append(pre);
        }
      }
      item.append(body);
      list.append(item);
    });
  }

  function renderAudit() {
    var section = document.getElementById("audit");
    section.replaceChildren();
    section.append(el("h3", null, "Audit log"));
    var list = el("ol");
    var rows = current.audit_before.slice();
    var branch = continuation();
    if (branch) rows = rows.concat(branch.audit);
    rows.forEach(function (row) {
      var item = el("li");
      item.append(el("span", null, row.event));
      item.append(document.createTextNode(row.actor));
      list.append(item);
    });
    section.append(list);
  }

  function renderCard() {
    var card = document.getElementById("card");
    card.replaceChildren();
    var branch = continuation();
    var ticket = el("div", "ticket");
    if (!branch) ticket.classList.add("is-wait");
    else if (branch.status === "completed" && phase === "edit") ticket.classList.add("is-edit");
    else if (branch.status === "completed") ticket.classList.add("is-ok");
    else if (branch.status === "expired") ticket.classList.add("is-expired");
    else ticket.classList.add("is-stop");

    var kicker = "Awaiting approval";
    if (clockJumped && !branch) kicker = "Clock is past expiry";
    else if (branch && branch.status === "completed" && phase === "edit") kicker = "Edited, then executed";
    else if (branch && branch.status === "completed") kicker = "Approved and executed";
    else if (branch && branch.status === "denied") kicker = "Denied";
    else if (branch && branch.status === "expired") kicker = "Expired";
    ticket.append(el("p", "kicker", kicker));
    ticket.append(el("h2", null, current.proposal.tool));
    ticket.append(el("p", "risk", current.proposal.risk_label + " · held for " + current.proposal.ttl_label));

    var rows = branch && branch.preview ? branch.preview : current.proposal.preview;
    var fields = el("dl", "fields");
    rows.forEach(function (row) {
      var wrap = el("div");
      wrap.append(el("dt", null, row.label));
      var dd = el("dd", row.label === "Body" ? "clamp" : null, row.value);
      wrap.append(dd);
      fields.append(wrap);
    });
    ticket.append(fields);
    ticket.append(el("p", "expiry", "expires " + current.proposal.expires_at));

    if (branch && branch.final_answer) {
      ticket.append(el("p", "footnote", branch.final_answer));
    }
    if (branch && branch.status === "denied") {
      ticket.append(el("p", "footnote", branch.reason || ""));
    }
    if (branch) {
      var count = branch.execution_count === 1 ? "Executed once." : "Executed " + branch.execution_count + " times.";
      if (branch.idempotent_replays) count += " Duplicate clicks: " + branch.idempotent_replays + ".";
      ticket.append(el("p", "footnote", count));
    }

    var actions = el("div", "actions");
    actions.append(actionButton("approve", "Approve", "#btn-approve"));
    actions.append(actionButton("deny", "Deny", "#btn-deny"));
    var edit = actionButton("edit", "Edit", "#btn-edit");
    if (!current.has_edit) edit.disabled = true;
    actions.append(edit);
    ticket.append(actions);

    if (showEdit && !branch && current.continuations.edit) {
      ticket.append(editPanel(current.continuations.edit));
    }

    var secondary = el("div", "secondary");
    var jump = el("button", "text-btn", clockJumped ? "Clock is past expiry" : "Jump clock past expiry");
    jump.type = "button";
    jump.id = "btn-jump";
    jump.disabled = Boolean(branch);
    jump.addEventListener("click", function () {
      clockJumped = true;
      showEdit = false;
      render();
    });
    var reset = el("button", "text-btn", "Reset");
    reset.type = "button";
    reset.id = "btn-reset";
    reset.addEventListener("click", function () {
      phase = "pending";
      clockJumped = false;
      showEdit = false;
      render();
    });
    secondary.append(jump, reset);
    ticket.append(secondary);
    ticket.append(el(
      "p",
      "footnote",
      "Replay only. The live gate re-validates any edit and is idempotent across process restarts."
    ));
    card.append(ticket);
  }

  function actionButton(name, label, idSelector) {
    var button = el("button", null, label);
    button.type = "button";
    button.id = idSelector.slice(1);
    button.disabled = continuation() != null || (name === "edit" && !current.has_edit);
    if (clockJumped && name !== "approve") button.disabled = true;
    if (clockJumped && name === "approve") button.textContent = "Submit late approve";
    button.addEventListener("click", function () {
      if (name === "edit" && !clockJumped) {
        showEdit = !showEdit;
        render();
        return;
      }
      phase = name;
      showEdit = false;
      render();
    });
    return button;
  }

  function editPanel(edit) {
    var panel = el("div", "diff");
    panel.append(el("p", null, "Recorded edit"));
    var proposed = current.proposal.arguments;
    var next = edit.edited_arguments;
    Object.keys(next).forEach(function (key) {
      if (proposed[key] === next[key]) return;
      panel.append(el("p", "minus", "− " + key + "  " + proposed[key]));
      panel.append(el("p", "plus", "+ " + key + "  " + next[key]));
    });
    if (edit.reason) panel.append(el("p", null, edit.reason));
    var apply = el("button", "apply", "Apply this edit");
    apply.type = "button";
    apply.id = "btn-apply-edit";
    apply.addEventListener("click", function () {
      phase = "edit";
      showEdit = false;
      render();
    });
    panel.append(apply);
    return panel;
  }

  function select(id) {
    current = data.runs.filter(function (run) { return run.id === id; })[0];
    phase = "pending";
    clockJumped = false;
    showEdit = false;
    render();
  }

  function themeLabel() {
    var toggle = document.getElementById("theme-toggle");
    var dark = document.documentElement.dataset.theme === "dark";
    toggle.textContent = dark ? "Light theme" : "Dark theme";
  }

  document.getElementById("theme-toggle").addEventListener("click", function () {
    var next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("hl-theme", next);
    themeLabel();
  });

  load().then(function (bundle) {
    if (!bundle || !bundle.runs) {
      document.body.textContent = "Missing site/data/runs.json";
      return;
    }
    data = bundle;
    var stamp = document.getElementById("stamp");
    stamp.textContent = "Recorded " + bundle.generated_at + " · " + bundle.provider + " provider · no backend";
    themeLabel();
    select(selectedId());
    window.addEventListener("hashchange", function () {
      var id = selectedId();
      if (!current || current.id !== id) select(id);
    });
  });
})();
