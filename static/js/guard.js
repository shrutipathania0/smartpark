// SmartPark AI — Guard Dashboard Logic

document.addEventListener("DOMContentLoaded", () => {
  const kpiTotal = document.getElementById("kpi-total");
  const kpiVacant = document.getElementById("kpi-vacant");
  const kpiBlocked = document.getElementById("kpi-blocked");
  const kpiActive = document.getElementById("kpi-active");
  const kpiReserved = document.getElementById("kpi-reserved");
  const kpiOccupied = document.getElementById("kpi-occupied");
  const kpiRevenue = document.getElementById("kpi-revenue");
  const kpiEntries = document.getElementById("kpi-entries");
  const kpiExits = document.getElementById("kpi-exits");
  const kpiAlerts = document.getElementById("kpi-alerts");
  const badgeAlertsCount = document.getElementById("badge-open-alerts-count");

  const alertsTableBody = document.getElementById("alerts-table-body");
  const btnRefreshAlerts = document.getElementById("btn-refresh-alerts");
  const recentActivityList = document.getElementById("recent-activity-list");
  const btnRefreshActivity = document.getElementById("btn-refresh-activity");

  const pricingTabs = document.querySelectorAll(".btn-pricing-tab");
  const priceFreeMin = document.getElementById("price-free-min");
  const priceGraceMin = document.getElementById("price-grace-min");
  const priceRate = document.getElementById("price-rate");
  const priceInterval = document.getElementById("price-interval");
  const pricePolicy = document.getElementById("price-policy");
  const btnSavePricing = document.getElementById("btn-save-pricing");
  const pricingFeedback = document.getElementById("pricing-feedback");

  let activeCategory = "Normal Parking";
  let cachedPricingRules = {};

  // 1. Fetch Dashboard Stats
  async function fetchDashboardStats() {
    try {
      const res = await fetch("/api/guard/dashboard");
      const data = await res.json();
      if (data.success) {
        const s = data.stats;
        kpiTotal.textContent = s.total_slots;
        kpiVacant.textContent = s.vacant_slots;
        kpiBlocked.textContent = s.blocked_slots;
        kpiActive.textContent = s.active_sessions;
        kpiReserved.textContent = s.reserved_slots;
        kpiOccupied.textContent = s.occupied_slots;
        kpiRevenue.textContent = `₹${s.revenue_today.toFixed(2)}`;
        kpiEntries.textContent = s.entries_today;
        kpiExits.textContent = s.exits_today;
        kpiAlerts.textContent = s.open_alerts;
        badgeAlertsCount.textContent = `${s.open_alerts} Open`;
      }
    } catch (e) {
      console.error("Error fetching stats:", e);
    }
  }

  // 2. Fetch and Render Alerts
  async function fetchAlerts() {
    try {
      const res = await fetch("/api/guard/alerts");
      const data = await res.json();
      if (data.success && data.alerts) {
        renderAlerts(data.alerts);
      }
    } catch (e) {
      console.error("Error fetching alerts:", e);
    }
  }

  function renderAlerts(alerts) {
    if (!alerts || alerts.length === 0) {
      alertsTableBody.innerHTML = `<tr><td colspan="6" style="padding: 1.5rem; text-align: center; color: var(--text-muted);">No incident alerts logged. Facility operational.</td></tr>`;
      return;
    }

    alertsTableBody.innerHTML = "";
    alerts.forEach(a => {
      const tr = document.createElement("tr");
      tr.style.borderBottom = "1px solid var(--border-color)";

      const sevColor = a.severity === "CRITICAL" ? "#f87171" : (a.severity === "WARNING" ? "#fde047" : "#38bdf8");
      const statusBadge = a.status === "OPEN" ? "badge-occupied" : (a.status === "ACKNOWLEDGED" ? "badge-reserved" : "badge-vacant");

      tr.innerHTML = `
        <td style="padding: 0.75rem 0.5rem; font-weight: 700;">${a.alert_type}</td>
        <td style="padding: 0.75rem 0.5rem;"><span style="color:${sevColor};font-weight:700;">● ${a.severity}</span></td>
        <td style="padding: 0.75rem 0.5rem;">${a.description}</td>
        <td style="padding: 0.75rem 0.5rem;"><span class="badge ${statusBadge}">${a.status}</span></td>
        <td style="padding: 0.75rem 0.5rem; color: var(--text-muted); font-size: 0.8rem;">${new Date(a.created_at).toLocaleTimeString()}</td>
        <td style="padding: 0.75rem 0.5rem; text-align: right;">
          ${a.status === 'OPEN' ? `<button class="btn btn-secondary btn-ack" data-id="${a.id}" style="padding:0.25rem 0.5rem;font-size:0.75rem;margin-right:0.3rem;">Ack</button>` : ""}
          ${a.status !== 'RESOLVED' ? `<button class="btn btn-success btn-resolve" data-id="${a.id}" style="padding:0.25rem 0.5rem;font-size:0.75rem;">Resolve</button>` : `<span style="color:#4ade80;font-size:0.8rem;">✓ Resolved</span>`}
        </td>
      `;
      alertsTableBody.appendChild(tr);
    });

    // Attach button listeners
    document.querySelectorAll(".btn-ack").forEach(b => {
      b.addEventListener("click", () => acknowledgeAlert(b.getAttribute("data-id")));
    });
    document.querySelectorAll(".btn-resolve").forEach(b => {
      b.addEventListener("click", () => resolveAlert(b.getAttribute("data-id")));
    });
  }

  async function acknowledgeAlert(id) {
    try {
      const res = await fetch(`/api/guard/alerts/${id}/acknowledge`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        fetchAlerts();
        fetchDashboardStats();
      }
    } catch (e) {}
  }

  async function resolveAlert(id) {
    try {
      const res = await fetch(`/api/guard/alerts/${id}/resolve`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        fetchAlerts();
        fetchDashboardStats();
      }
    } catch (e) {}
  }

  // 3. Pricing Configuration Logic
  async function fetchPricingRules() {
    try {
      const res = await fetch("/api/guard/pricing");
      const data = await res.json();
      if (data.success && data.pricing_rules) {
        data.pricing_rules.forEach(r => {
          cachedPricingRules[r.category] = r;
        });
        loadActiveCategoryPricing();
      }
    } catch (e) {
      console.error("Error fetching pricing:", e);
    }
  }

  function loadActiveCategoryPricing() {
    const r = cachedPricingRules[activeCategory];
    if (r) {
      priceFreeMin.value = r.free_minutes;
      priceGraceMin.value = r.grace_minutes;
      priceRate.value = r.charge_amount;
      priceInterval.value = r.billing_interval_minutes;
      pricePolicy.value = r.rounding_policy;
    }
  }

  pricingTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      pricingTabs.forEach(t => t.classList.remove("active", "btn-primary"));
      pricingTabs.forEach(t => t.classList.add("btn-secondary"));
      tab.classList.remove("btn-secondary");
      tab.classList.add("active", "btn-primary");
      activeCategory = tab.getAttribute("data-cat");
      loadActiveCategoryPricing();
      pricingFeedback.style.display = "none";
    });
  });

  btnSavePricing.addEventListener("click", async () => {
    const payload = {
      category: activeCategory,
      free_minutes: parseInt(priceFreeMin.value),
      grace_minutes: parseInt(priceGraceMin.value),
      charge_amount: parseFloat(priceRate.value),
      billing_interval_minutes: parseInt(priceInterval.value),
      rounding_policy: pricePolicy.value
    };

    btnSavePricing.disabled = true;
    btnSavePricing.textContent = "Updating...";

    try {
      const res = await fetch("/api/guard/pricing", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        cachedPricingRules[activeCategory] = data.pricing_rule;
        pricingFeedback.style.display = "flex";
        pricingFeedback.className = "alert-banner alert-info";
        pricingFeedback.innerHTML = `<span>Pricing updated for <strong>${activeCategory}</strong>. Applies to future sessions.</span>`;
      } else {
        pricingFeedback.style.display = "flex";
        pricingFeedback.className = "alert-banner alert-danger";
        pricingFeedback.textContent = data.error || "Update failed.";
      }
    } catch (e) {
      pricingFeedback.style.display = "flex";
      pricingFeedback.className = "alert-banner alert-danger";
      pricingFeedback.textContent = "Network error updating rates.";
    } finally {
      btnSavePricing.disabled = false;
      btnSavePricing.textContent = "Save Pricing Settings";
    }
  });

  // 4. Recent Vehicle Movements
  async function fetchRecentActivity() {
    try {
      const res = await fetch("/api/guard/recent-activity");
      const data = await res.json();
      if (data.success) {
        renderRecentActivity(data.recent_sessions);
      }
    } catch (e) {}
  }

  function renderRecentActivity(sessions) {
    if (!sessions || sessions.length === 0) {
      recentActivityList.innerHTML = `<div style="color:var(--text-muted);text-align:center;padding:1rem;">No recent vehicle activity.</div>`;
      return;
    }

    recentActivityList.innerHTML = "";
    sessions.forEach(s => {
      const div = document.createElement("div");
      div.style.padding = "0.75rem";
      div.style.background = "var(--bg-card)";
      div.style.borderRadius = "6px";
      div.style.border = "1px solid var(--border-color)";
      div.style.display = "flex";
      div.style.justifyContent = "space-between";
      div.style.alignItems = "center";

      const statusBadge = s.status === "COMPLETED" ? "badge-vacant" : (s.status === "ACTIVE_PARKED" ? "badge-occupied" : "badge-reserved");

      div.innerHTML = `
        <div>
          <div style="font-weight: 700; font-size: 1rem; color: var(--accent-blue);">${s.registration_number} <span style="font-size:0.75rem;color:var(--text-muted);">${s.parking_category}</span></div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">Slot: ${s.slot_number || 'N/A'} | Entry: ${new Date(s.entry_time).toLocaleTimeString()}</div>
        </div>
        <div style="text-align: right;">
          <span class="badge ${statusBadge}">${s.status}</span>
          <div style="font-weight: 800; font-size: 0.95rem; color: #4ade80; margin-top: 0.2rem;">${s.final_amount > 0 ? '₹' + s.final_amount.toFixed(2) : (s.status === 'COMPLETED' ? '₹0.00' : 'In Progress')}</div>
        </div>
      `;
      recentActivityList.appendChild(div);
    });
  }

  btnRefreshAlerts.addEventListener("click", fetchAlerts);
  btnRefreshActivity.addEventListener("click", fetchRecentActivity);

  // Initial load & 3s polling
  fetchDashboardStats();
  fetchAlerts();
  fetchPricingRules();
  fetchRecentActivity();

  setInterval(() => {
    fetchDashboardStats();
    fetchAlerts();
    fetchRecentActivity();
  }, 3000);
});

