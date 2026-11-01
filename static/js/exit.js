// SmartPark AI — Driver Exit Machine Logic

document.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("exit-webcam-video");
  const canvas = document.getElementById("exit-detection-canvas");
  const placeholder = document.getElementById("exit-cam-placeholder");
  const btnStartCam = document.getElementById("btn-start-exit-cam");
  const btnScanExit = document.getElementById("btn-scan-exit");
  const regInput = document.getElementById("exit-reg-input");
  const btnLookup = document.getElementById("btn-lookup-session");
  const alertBox = document.getElementById("exit-alert-box");

  const previewPanel = document.getElementById("exit-anpr-preview");
  const croppedImg = document.getElementById("exit-cropped-plate");
  const recText = document.getElementById("exit-rec-text");
  const confBadge = document.getElementById("exit-conf-badge");

  const billingPanel = document.getElementById("billing-panel");
  const billTktId = document.getElementById("bill-tkt-id");
  const billStatus = document.getElementById("bill-session-status");
  const billReg = document.getElementById("bill-reg");
  const billSlotCat = document.getElementById("bill-slot-cat");
  const billStartTime = document.getElementById("bill-start-time");
  const billDuration = document.getElementById("bill-duration");
  const billFreePeriod = document.getElementById("bill-free-period");
  const billChargeableTime = document.getElementById("bill-chargeable-time");
  const billBlocksRate = document.getElementById("bill-blocks-rate");
  const billTotalAmount = document.getElementById("bill-total-amount");

  const btnConfirmExit = document.getElementById("btn-confirm-exit");
  const btnCancelReservation = document.getElementById("btn-cancel-reservation");
  const receiptDisplay = document.getElementById("receipt-display");
  const quickActiveBtns = document.getElementById("quick-active-buttons");

  let stream = null;
  let activeSessionData = null;

  function showAlert(message, type = "danger") {
    alertBox.style.display = "flex";
    alertBox.className = `alert-banner alert-${type}`;
    alertBox.innerHTML = `<span>${message}</span><button type="button" onclick="this.parentElement.style.display='none'" style="background:none;border:none;color:inherit;cursor:pointer;font-weight:bold;">&times;</button>`;
  }

  function drawBbox(bbox) {
    if (!bbox || bbox.length < 4) return;
    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const [x1, y1, x2, y2] = bbox;
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 4;
    ctx.fillStyle = "rgba(239, 68, 68, 0.2)";
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.fillRect(x1, y1, x2 - x1, y2 - y1);

    ctx.fillStyle = "#ef4444";
    ctx.fillRect(x1, Math.max(0, y1 - 24), 130, 24);
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 14px sans-serif";
    ctx.fillText("EXIT SCAN", x1 + 6, Math.max(16, y1 - 7));
  }

  // 1. Camera Controls
  async function startCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }
      });
      video.srcObject = stream;
      video.style.display = "block";
      placeholder.style.display = "none";
      btnStartCam.textContent = "Stop Camera";
      btnStartCam.className = "btn btn-secondary";
      showAlert("Exit camera active. Scan departing vehicle plate.", "info");
    } catch (err) {
      showAlert(`Camera Error: ${err.message}. Manual lookup available.`, "warning");
    }
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    video.style.display = "none";
    placeholder.style.display = "block";
    btnStartCam.textContent = "Start Camera";
    btnStartCam.className = "btn btn-primary";
  }

  btnStartCam.addEventListener("click", () => {
    if (stream) stopCamera();
    else startCamera();
  });

  // 2. Scan Frame
  async function scanExitPlate() {
    if (!stream && video.style.display !== "block") {
      showAlert("Please start the camera or enter vehicle plate manually.", "warning");
      return;
    }

    const offscreen = document.createElement("canvas");
    offscreen.width = video.videoWidth || 640;
    offscreen.height = video.videoHeight || 480;
    const ctx = offscreen.getContext("2d");
    ctx.drawImage(video, 0, 0, offscreen.width, offscreen.height);
    const dataUrl = offscreen.toDataURL("image/jpeg", 0.85);

    btnScanExit.disabled = true;
    btnScanExit.textContent = "Scanning...";

    try {
      const resp = await fetch("/api/exit/recognize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frame: dataUrl })
      });
      const data = await resp.json();

      if (data.success) {
        if (data.bbox) drawBbox(data.bbox);
        if (data.cropped_plate_b64) {
          previewPanel.style.display = "block";
          croppedImg.src = data.cropped_plate_b64;
        }

        const reg = data.registration_number || data.raw_text;
        recText.textContent = reg || "NO TEXT DETECTED";

        confBadge.className = "badge";
        if (data.confidence_tier === "HIGH") {
          confBadge.classList.add("badge-high");
          confBadge.textContent = `HIGH (${Math.round(data.combined_confidence * 100)}%)`;
        } else {
          confBadge.classList.add("badge-med");
          confBadge.textContent = `CONFIRM (${Math.round(data.combined_confidence * 100)}%)`;
        }

        if (reg) {
          regInput.value = reg;
          // Auto-lookup active session
          lookupSession(reg);
        } else {
          showAlert("Plate detected but text unclear. Please enter manually.", "warning");
        }
      } else {
        showAlert(data.error || "Exit scan failed.", "warning");
      }
    } catch (e) {
      showAlert("ANPR processing error.", "danger");
    } finally {
      btnScanExit.disabled = false;
      btnScanExit.textContent = "Scan Vehicle";
    }
  }

  btnScanExit.addEventListener("click", scanExitPlate);

  // 3. Lookup Session
  async function lookupSession(reg) {
    if (!reg) reg = regInput.value.trim().toUpperCase();
    if (!reg) {
      showAlert("Please enter a vehicle registration number to search.", "warning");
      return;
    }

    btnLookup.disabled = true;
    btnLookup.textContent = "Searching...";

    try {
      const res = await fetch(`/api/exit/session/${encodeURIComponent(reg)}`);
      const data = await res.json();

      if (data.success) {
        activeSessionData = data.session;
        renderBilling(data.session, data.bill);
        showAlert(`Active session retrieved for ${reg}.`, "info");
      } else {
        billingPanel.style.display = "none";
        showAlert(data.error || `No active parking session found for ${reg}.`, "danger");
      }
    } catch (e) {
      showAlert("Network error retrieving session.", "danger");
    } finally {
      btnLookup.disabled = false;
      btnLookup.textContent = "Find";
    }
  }

  btnLookup.addEventListener("click", () => lookupSession());

  // 4. Render Itemized Bill
  function renderBilling(session, bill) {
    billingPanel.style.display = "block";
    receiptDisplay.style.display = "none";

    billTktId.textContent = session.ticket_id;
    billStatus.textContent = session.status;
    billStatus.className = `badge ${session.status === 'ACTIVE_PARKED' ? 'badge-occupied' : 'badge-reserved'}`;

    billReg.textContent = session.registration_number;
    billSlotCat.textContent = `${session.slot_number || 'N/A'} (${session.parking_category})`;

    if (session.parked_start_time) {
      billStartTime.textContent = new Date(session.parked_start_time).toLocaleTimeString();
      billDuration.textContent = `${bill.total_duration_minutes} min (${Math.floor(bill.actual_duration_seconds / 60)}m ${bill.actual_duration_seconds % 60}s)`;
      btnCancelReservation.style.display = "none";
    } else {
      billStartTime.textContent = "Not Parked (Reserved Only)";
      billDuration.textContent = "0 min";
      btnCancelReservation.style.display = "inline-block";
    }

    billFreePeriod.textContent = `${bill.free_minutes} min free + ${bill.grace_minutes} min grace (${bill.total_free_minutes} min total)`;
    billChargeableTime.textContent = `${bill.chargeable_duration_minutes} minutes`;
    billBlocksRate.textContent = `${bill.number_of_blocks} block(s) × ₹${bill.rate_per_block.toFixed(2)} per ${bill.billing_interval_minutes}m`;
    billTotalAmount.textContent = `₹${bill.final_amount.toFixed(2)}`;
  }

  // 5. Confirm Exit
  btnConfirmExit.addEventListener("click", async () => {
    if (!activeSessionData) return;

    btnConfirmExit.disabled = true;
    btnConfirmExit.textContent = "Processing Exit...";

    try {
      const res = await fetch("/api/exit/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: activeSessionData.id })
      });
      const data = await res.json();

      if (data.success) {
        billingPanel.style.display = "none";
        receiptDisplay.style.display = "block";

        document.getElementById("rec-released-bay").textContent = data.slot ? data.slot.slot_number : "Released";
        document.getElementById("rec-id").textContent = data.session.ticket_id;
        document.getElementById("rec-paid-amount").textContent = `₹${data.session.final_amount.toFixed(2)}`;
        document.getElementById("rec-exit-time").textContent = new Date(data.session.exit_time).toLocaleString();

        showAlert(`Exit complete! Bay ${data.slot ? data.slot.slot_number : ''} is now VACANT (Green).`, "info");
        refreshActiveVehicles();
      } else {
        showAlert(data.error || "Failed to finalize exit.", "danger");
      }
    } catch (e) {
      showAlert("Network error during exit completion.", "danger");
    } finally {
      btnConfirmExit.disabled = false;
      btnConfirmExit.textContent = "💳 Confirm Exit & Release Bay";
    }
  });

  // Cancel reservation
  btnCancelReservation.addEventListener("click", async () => {
    if (!activeSessionData) return;
    if (!confirm("Confirm cancellation of unparked reservation? Assigned bay will be released without charge.")) return;

    try {
      const res = await fetch("/api/exit/cancel-reservation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: activeSessionData.id })
      });
      const data = await res.json();
      if (data.success) {
        billingPanel.style.display = "none";
        showAlert("Reservation cancelled. Bay released to VACANT without charge.", "info");
        refreshActiveVehicles();
      }
    } catch (e) {}
  });

  // 6. Refresh Quick Active Buttons
  async function refreshActiveVehicles() {
    try {
      const res = await fetch("/api/parking/slots");
      const d = await res.json();
      if (d.success) {
        const active = d.slots.filter(s => s.registration_number);
        if (active.length === 0) {
          quickActiveBtns.innerHTML = `<span style="font-size:0.8rem;color:var(--text-muted);">No active parked sessions yet. Create one at Entry.</span>`;
        } else {
          quickActiveBtns.innerHTML = "";
          active.forEach(s => {
            const btn = document.createElement("button");
            btn.className = "btn btn-secondary";
            btn.style.padding = "0.3rem 0.6rem";
            btn.style.fontSize = "0.8rem";
            btn.textContent = `${s.registration_number} (${s.slot_number} - ${s.status})`;
            btn.addEventListener("click", () => {
              regInput.value = s.registration_number;
              lookupSession(s.registration_number);
            });
            quickActiveBtns.appendChild(btn);
          });
        }
      }
    } catch (e) {}
  }

  refreshActiveVehicles();
  setInterval(refreshActiveVehicles, 3500);
});

