const LOCAL_USER_ID = "local_user";

const logEl = document.getElementById("log");
const healthBadge = document.getElementById("healthBadge");
const appTable = document.getElementById("applications");
const jobsTable = document.getElementById("jobsTable");
const selectedJobIds = new Set();

function syncSpecificJobInput() {
  const input = document.querySelector("#specificApplyForm input[name='job_ids']");
  if (input) {
    input.value = Array.from(selectedJobIds).join(", ");
  }
}

function logLine(message, data) {
  const stamp = new Date().toISOString();
  const payload = data ? ` ${JSON.stringify(data, null, 2)}` : "";
  logEl.textContent = `[${stamp}] ${message}${payload}\n` + logEl.textContent;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new Error(body?.detail || `HTTP ${res.status}`);
  }
  return body;
}

function parseList(text) {
  return (text || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function getFormData(form) {
  const fd = new FormData(form);
  return Object.fromEntries(fd.entries());
}

function toBool(value) {
  return value === "on" || value === true;
}

async function checkHealth() {
  try {
    await api("/health");
    healthBadge.textContent = "API Healthy";
    healthBadge.className = "badge badge-ok";
  } catch {
    healthBadge.textContent = "API Unreachable";
    healthBadge.className = "badge badge-err";
  }
}

async function refreshApplications() {
  try {
    const apps = await api("/applications");
    if (!apps.length) {
      appTable.innerHTML = "<p>No applications yet.</p>";
      return;
    }
    const rows = apps
      .slice()
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
      .map((app) => `
        <tr>
          <td>${app.application_id}</td>
          <td>${app.job_id}</td>
          <td><span class="status-pill status-${app.status}">${app.status}</span></td>
          <td>${new Date(app.updated_at).toLocaleString()}</td>
        </tr>`)
      .join("");
    appTable.innerHTML = `
      <table class="table">
        <thead>
          <tr><th>Application ID</th><th>Job ID</th><th>Status</th><th>Updated</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;
  } catch (err) {
    logLine("Failed to load applications", { error: String(err) });
  }
}

async function refreshJobs() {
  try {
    const jobs = await api("/jobs");
    if (!jobs.length) {
      jobsTable.innerHTML = "<p>No jobs discovered yet.</p>";
      return;
    }
    const rows = jobs
      .slice()
      .reverse()
      .slice(0, 100)
      .map((job) => `
        <tr>
          <td><input class="jobs-select" type="checkbox" data-job-id="${job.job_id}" ${selectedJobIds.has(job.job_id) ? "checked" : ""} /></td>
          <td>${job.job_id}</td>
          <td>${job.title}</td>
          <td>${job.company}</td>
          <td>${job.location}</td>
          <td>${job.source}</td>
        </tr>`)
      .join("");
    jobsTable.innerHTML = `
      <table class="table">
        <thead>
          <tr><th><input id="selectAllJobs" class="jobs-select" type="checkbox" /></th><th>Job ID</th><th>Title</th><th>Company</th><th>Location</th><th>Source</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;

    jobsTable.querySelectorAll(".jobs-select[data-job-id]").forEach((checkbox) => {
      checkbox.addEventListener("change", (event) => {
        const id = event.target.getAttribute("data-job-id");
        if (!id) return;
        if (event.target.checked) selectedJobIds.add(id);
        else selectedJobIds.delete(id);
        syncSpecificJobInput();
      });
    });

    const selectAll = document.getElementById("selectAllJobs");
    if (selectAll) {
      selectAll.checked = jobsTable.querySelectorAll(".jobs-select[data-job-id]").length > 0
        && Array.from(jobsTable.querySelectorAll(".jobs-select[data-job-id]")).every((el) => el.checked);
      selectAll.addEventListener("change", (event) => {
        jobsTable.querySelectorAll(".jobs-select[data-job-id]").forEach((checkbox) => {
          checkbox.checked = event.target.checked;
          const id = checkbox.getAttribute("data-job-id");
          if (!id) return;
          if (event.target.checked) selectedJobIds.add(id);
          else selectedJobIds.delete(id);
        });
        syncSpecificJobInput();
      });
    }
    syncSpecificJobInput();
  } catch (err) {
    logLine("Failed to load discovered jobs", { error: String(err) });
  }
}

document.getElementById("profileForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const payload = {
    user_id: LOCAL_USER_ID,
    full_name: data.full_name,
    email: data.email,
    locations: parseList(data.locations),
    target_titles: parseList(data.target_titles),
    required_salary_min: data.required_salary_min ? Number(data.required_salary_min) : null,
    allowed_job_types: ["full_time"],
    remote_ok: toBool(data.remote_ok),
  };
  try {
    const result = await api("/users", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    logLine("Profile saved", result);
  } catch (err) {
    logLine("Profile save failed", { error: String(err) });
  }
});

document.getElementById("resumeForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  try {
    const result = await api("/resume", {
      method: "POST",
      body: JSON.stringify({ user_id: LOCAL_USER_ID, resume_text: data.resume_text }),
    });
    logLine("Resume parsed", { skills: result.skills, years_experience: result.years_experience });
  } catch (err) {
    logLine("Resume parse failed", { error: String(err) });
  }
});

document.getElementById("discoverApplyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const payload = {
    user_id: LOCAL_USER_ID,
    query: data.query,
    search_sources: parseList(data.search_sources),
    additional_queries: parseList(data.additional_queries),
    focus_fields: parseList(data.focus_fields),
    include_titles: parseList(data.include_titles),
    exclude_titles: parseList(data.exclude_titles),
    education_levels: parseList(data.education_levels),
    location: data.location || null,
    remote_only: toBool(data.remote_only),
    limit: Number(data.limit || 25),
    min_ai_score: Number(data.min_ai_score || 70),
    max_apply: Number(data.max_apply || 10),
  };
  try {
    const result = await api("/automation/discover-and-auto-apply", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    logLine("Discovery + auto-apply complete", {
      provider: result.provider,
      discovered_jobs: result.discovered_jobs,
      qualified_jobs: result.qualified_jobs,
      submitted: result.submitted,
      needs_user_input: result.needs_user_input,
      top_matches: result.assessments.slice(0, 3).map((x) => ({ job_id: x.job_id, score: x.score })),
    });
    await refreshApplications();
    await refreshJobs();
  } catch (err) {
    logLine("Discover + auto-apply failed", { error: String(err) });
  }
});

document.getElementById("adapterForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const payload = {
    user_id: LOCAL_USER_ID,
    job_id: data.job_id,
    provider: data.provider,
    storage_state_path: data.storage_state_path || null,
  };
  try {
    const result = await api("/applications/browser-apply", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    logLine("Browser adapter apply result", result);
    await refreshApplications();
  } catch (err) {
    logLine("Browser adapter apply failed", { error: String(err) });
  }
});

document.getElementById("specificApplyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = getFormData(event.currentTarget);
  const payload = {
    user_id: LOCAL_USER_ID,
    job_ids: parseList(data.job_ids),
    min_ai_score: Number(data.min_ai_score || 60),
    max_apply: Number(data.max_apply || 25),
  };
  try {
    const result = await api("/automation/auto-apply-specific", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    logLine("Specific job auto-apply complete", {
      submitted: result.submitted,
      needs_user_input: result.needs_user_input,
      qualified_jobs: result.qualified_jobs,
    });
    await refreshApplications();
    await refreshJobs();
  } catch (err) {
    logLine("Specific job auto-apply failed", { error: String(err) });
  }
});

document.getElementById("refreshApps").addEventListener("click", refreshApplications);
document.getElementById("refreshJobs").addEventListener("click", refreshJobs);
document.getElementById("applySelectedJobs").addEventListener("click", async () => {
  if (!selectedJobIds.size) {
    logLine("No jobs selected", { hint: "Select one or more jobs in the Discovered Jobs table." });
    return;
  }
  const specificForm = document.getElementById("specificApplyForm");
  const data = getFormData(specificForm);
  const payload = {
    user_id: LOCAL_USER_ID,
    job_ids: Array.from(selectedJobIds),
    min_ai_score: Number(data.min_ai_score || 60),
    max_apply: Number(data.max_apply || 25),
  };
  try {
    const result = await api("/automation/auto-apply-specific", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    logLine("Selected jobs auto-apply complete", {
      selected: payload.job_ids.length,
      submitted: result.submitted,
      needs_user_input: result.needs_user_input,
    });
    await refreshApplications();
  } catch (err) {
    logLine("Selected jobs auto-apply failed", { error: String(err) });
  }
});

logLine("Local mode active", { user_id: LOCAL_USER_ID });
checkHealth();
refreshApplications();
refreshJobs();
