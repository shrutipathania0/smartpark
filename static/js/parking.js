// SmartPark AI — Parking Area Monitoring & Simulation Logic

document.addEventListener("DOMContentLoaded", () => {
  const containerDisabled = document.getElementById("container-disabled");
  const containerEv = document.getElementById("container-ev");
  const containerNormal = document.getElementById("container-normal");
  const simAlertBox = document.getElementById("sim-alert-box");
  const blockSelect = document.getElementById("sim-block-slot-select");
  const clearSelect = document.getElementById("sim-clear-slot-select");
  const btnPlaceObstacle = document.getElementById("btn-place-obstacle");
  const btnClearObstacle = document.getElementById("btn-clear-obstacle");
  const btnResetSim = document.getElementById("btn-reset-sim");

  const modal = document.getElementById("slot-modal");
  const modalTitle = document.getElementById("modal-slot-title");
  const modalContent = document.getElementById("modal-slot-content");

  let currentSlots = [];

  function showSimAlert(msg, type = "info") {
    simAlertBox.style.display = "flex";
    simAlertBox.className = `alert-banner alert-${type}`;
    simAlertBox.innerHTML = `<span>${msg}</span><button type="button" onclick="this.parentElement.style.display='none'" style="background:none;border:none;color:inherit;cursor:pointer;font-weight:bold;">&times;</button>`;
  }

  // Render slot cards into their respective category containers
  function renderSlots(slots) {
    currentSlots = slots;
    containerDisabled.innerHTML = "";
    containerEv.innerHTML = "";
    containerNormal.innerHTML = "";

    // Clear selects
    blockSelect.innerHTML = "";
    clearSelect.innerHTML = "";

    slots.forEach(slot => {
      const statusLower = slot.status.toLowerCase(); // vacant, reserved, occupied, blocked
      const card = document.createElement("div");
      card.className = `parking-slot-card slot-${statusLower}`;
      card.setAttribute("data-id", slot.id);

      // Icon based on category and status
      let icon = "🚗";
      if (slot.category === "Disabled Parking") icon = "♿";
      else if (slot.category === "EV Charging Parking") icon = "⚡";

      if (slot.status === "BLOCKED") icon = "🚧";

      card.innerHTML = `
        <div class="slot-id-label">${slot.slot_number}</div>
        <div class="slot-car-icon">${icon}</div>
        <span class="badge badge-${statusLower}">${slot.status}</span>
        ${slot.registration_number ? `<div class="slot-reg-tag">${slot.registration_number}</div>` : ""}
      `;

      card.addEventListener("click", () => showSlotDetails(slot));

      // Append to category container
      if (slot.category === "Disabled Parking") {
        containerDisabled.appendChild(card);
      } else if (slot.category === "EV Charging Parking") {
        containerEv.appendChild(card);
      } else {
        containerNormal.appendChild(card);
      }

      // Populate simulation selects
      const opt = document.createElement("option");
      opt.value = slot.id;
      opt.textContent = `${slot.slot_number} (${slot.status})`;

      if (slot.status !== "BLOCKED") {
        blockSelect.appendChild(opt);
      } else {
        clearSelect.appendChild(opt);
      }
    });

    if (blockSelect.options.length === 0) {
      blockSelect.innerHTML = "<option disabled>No slots</option>";
    }
    if (clearSelect.options.length === 0) {
      clearSelect.innerHTML = "<option disabled>No blocked slots</option>";
    }
  }

  // Show Modal with slot & active session details
  function showSlotDetails(slot) {
    modalTitle.textContent = `Bay ${slot.slot_number} Details`;
    modalContent.innerHTML = `
      <div style="margin-bottom: 0.75rem;">
        <span class="label" style="color:var(--text-muted);font-size:0.85rem;">Category:</span>
        <div style="font-weight:700;font-size:1.05rem;">${slot.category}</div>
      </div>
      <div style="margin-bottom: 0.75rem;">
        <span class="label" style="color:var(--text-muted);font-size:0.85rem;">Current Status:</span>
        <div><span class="badge badge-${slot.status.toLowerCase()}">${slot.status}</span></div>
      </div>
      ${slot.registration_number ? `
        <div style="margin-bottom: 0.75rem;">
          <span class="label" style="color:var(--text-muted);font-size:0.85rem;">Assigned Vehicle:</span>
          <div style="font-weight:800;font-size:1.2rem;color:var(--accent-blue);">${slot.registration_number}</div>
        </div>
      ` : ""}
      ${slot.ticket_id ? `
        <div style="margin-bottom: 0.75rem;">
          <span class="label" style="color:var(--text-muted);font-size:0.85rem;">Active Ticket:</span>
          <div style="font-family:monospace;font-size:1rem;color:#fde047;">${slot.ticket_id}</div>
        </div>
      ` : ""}
      ${slot.parked_start_time ? `
        <div style="margin-bottom: 0.75rem;">
          <span class="label" style="color:var(--text-muted);font-size:0.85rem;">Actual Parked Start Time:</span>
          <div>${new Date(slot.parked_start_time).toLocaleString()}</div>
        </div>
      ` : (slot.status === 'RESERVED' ? `<div style="font-size:0.85rem;color:#fde047;">Vehicle en route. Billing timer will start when physical parking is verified.</div>` : "")}
    `;
    modal.style.display = "flex";
  }

  // Fetch slot status from backend
  async function fetchSlots() {
    try {
      const res = await fetch("/api/parking/slots");
      const data = await res.json();
      if (data.success) {
        renderSlots(data.slots);
      }
    } catch (e) {
      console.error("Error fetching slots:", e);
    }
  }

  // Generic simulation trigger
  async function triggerSimulation(action, payload = {}) {
    try {
      const res = await fetch("/api/parking/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, ...payload })
      });
      const data = await res.json();
      if (data.success) {
        showSimAlert(`Simulation Action [${action}] succeeded. Facility updated.`, "info");
        fetchSlots();
      } else {
        showSimAlert(data.error || "Simulation action failed", "warning");
      }
    } catch (err) {
      showSimAlert("Network error triggering simulation", "danger");
    }
  }

  // Event handlers for simulation controls
  document.querySelectorAll(".btn-sim[data-action]").forEach(btn => {
    btn.addEventListener("click", () => {
      const action = btn.getAttribute("data-action");
      triggerSimulation(action);
    });
  });

  btnPlaceObstacle.addEventListener("click", () => {
    const slotId = parseInt(blockSelect.value);
    if (!slotId) return;
    triggerSimulation("place_object", { slot_id: slotId, description: "Maintenance cone placed" });
  });

  btnClearObstacle.addEventListener("click", () => {
    const slotId = parseInt(clearSelect.value);
    if (!slotId) return;
    triggerSimulation("clear_object", { slot_id: slotId });
  });

  btnResetSim.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to reset all parking bays to VACANT? Active demo sessions will be cleared.")) return;
    try {
      const res = await fetch("/api/parking/reset", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        showSimAlert("Simulation bays reset to VACANT state successfully.", "info");
        fetchSlots();
      }
    } catch (e) {
      showSimAlert("Reset failed", "danger");
    }
  });

  // Initial fetch and auto-sync poll every 2.5 seconds
  fetchSlots();
  setInterval(fetchSlots, 2500);
});

