// SmartPark AI — Driver Entry Machine Logic

document.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("webcam-video");
  const canvas = document.getElementById("detection-canvas");
  const placeholder = document.getElementById("cam-placeholder");
  const btnStartCam = document.getElementById("btn-start-cam");
  const btnCapture = document.getElementById("btn-capture-frame");
  const regInput = document.getElementById("reg-number-input");
  const btnClearReg = document.getElementById("btn-clear-reg");
  const btnAllocate = document.getElementById("btn-allocate-slot");
  const alertBox = document.getElementById("entry-alert-box");
  const previewPanel = document.getElementById("anpr-preview-panel");
  const croppedPlateImg = document.getElementById("cropped-plate-img");
  const recTextDisplay = document.getElementById("recognized-text-display");
  const confBadge = document.getElementById("confidence-badge");
  const ticketDisplay = document.getElementById("ticket-display");

  let stream = null;
  let isScanning = false;

  // Helper to show alert banner
  function showAlert(message, type = "danger") {
    alertBox.style.display = "flex";
    alertBox.className = `alert-banner alert-${type}`;
    alertBox.innerHTML = `<span>${message}</span><button type="button" onclick="this.parentElement.style.display='none'" style="background:none;border:none;color:inherit;cursor:pointer;font-weight:bold;">&times;</button>`;
  }

  // Helper to draw bounding box on video overlay canvas
  function drawBbox(bbox) {
    if (!bbox || bbox.length < 4) return;
    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const [x1, y1, x2, y2] = bbox;
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 4;
    ctx.fillStyle = "rgba(56, 189, 248, 0.2)";
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.fillRect(x1, y1, x2 - x1, y2 - y1);

    // Label tag
    ctx.fillStyle = "#38bdf8";
    ctx.fillRect(x1, Math.max(0, y1 - 24), 130, 24);
    ctx.fillStyle = "#0f172a";
    ctx.font = "bold 14px sans-serif";
    ctx.fillText("NUMBER PLATE", x1 + 6, Math.max(16, y1 - 7));
  }

  // 1. Start Webcam
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
      showAlert("Webcam connected. Align vehicle number plate within frame.", "info");
    } catch (err) {
      console.error("Camera access error:", err);
      showAlert(`Camera Error: ${err.message}. You can use sample test plates or manual entry below.`, "warning");
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
    if (stream) {
      stopCamera();
    } else {
      startCamera();
    }
  });

  // 2. Capture and Send Frame to Backend ANPR
  async function captureAndScan() {
    if (!stream && video.style.display !== "block") {
      showAlert("Please start the webcam or click one of the instant demo test buttons.", "warning");
      return;
    }

    const offscreen = document.createElement("canvas");
    offscreen.width = video.videoWidth || 640;
    offscreen.height = video.videoHeight || 480;
    const ctx = offscreen.getContext("2d");
    ctx.drawImage(video, 0, 0, offscreen.width, offscreen.height);
    const dataUrl = offscreen.toDataURL("image/jpeg", 0.85);

    btnCapture.disabled = true;
    btnCapture.textContent = "Scanning...";

    try {
      const resp = await fetch("/api/entry/recognize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frame: dataUrl })
      });
      const data = await resp.json();

      if (data.success) {
        handleAnprResult(data);
      } else {
        showAlert(data.error || "ANPR Scan failed.", "warning");
      }
    } catch (err) {
      showAlert("Failed to communicate with ANPR recognition server.", "danger");
    } finally {
      btnCapture.disabled = false;
      btnCapture.textContent = "Capture & Scan";
    }
  }

  btnCapture.addEventListener("click", captureAndScan);

  // 3. Process ANPR response
  function handleAnprResult(data) {
    if (data.bbox) {
      drawBbox(data.bbox);
    }

    if (data.cropped_plate_b64) {
      previewPanel.style.display = "block";
      croppedPlateImg.src = data.cropped_plate_b64;
    }

    const reg = data.registration_number || data.raw_text;
    recTextDisplay.textContent = reg || "NO TEXT DETECTED";

    // Set confidence badge
    confBadge.className = "badge";
    if (data.confidence_tier === "HIGH") {
      confBadge.classList.add("badge-high");
      confBadge.textContent = `HIGH CONFIDENCE (${Math.round(data.combined_confidence * 100)}%)`;
      regInput.value = reg;
      showAlert(`High-confidence plate detected: ${reg}. Field auto-populated.`, "info");
    } else if (data.confidence_tier === "MEDIUM") {
      confBadge.classList.add("badge-med");
      confBadge.textContent = `CONFIRM (${Math.round(data.combined_confidence * 100)}%)`;
      regInput.value = reg;
      showAlert(`Detected plate candidate: ${reg}. Please verify before allocating.`, "warning");
    } else {
      confBadge.classList.add("badge-low");
      confBadge.textContent = `LOW CONFIDENCE`;
      if (reg) regInput.value = reg;
      showAlert("Low confidence recognition. Please confirm or manually edit registration.", "warning");
    }
  }

  // 4. Sample Test Buttons
  document.querySelectorAll(".btn-sample").forEach(btn => {
    btn.addEventListener("click", () => {
      const plate = btn.getAttribute("data-plate");
      const cat = btn.getAttribute("data-cat");

      regInput.value = plate;
      const radio = document.querySelector(`input[name="parking_category"][value="${cat}"]`);
      if (radio) radio.checked = true;

      // Update preview display
      previewPanel.style.display = "block";
      recTextDisplay.textContent = plate;
      confBadge.className = "badge badge-high";
      confBadge.textContent = "DEMO BENCHMARK (100%)";

      showAlert(`Selected benchmark vehicle ${plate} (${cat}). Ready to allocate.`, "info");
    });
  });

  btnClearReg.addEventListener("click", () => {
    regInput.value = "";
    previewPanel.style.display = "none";
  });

  // 5. Allocate Slot
  btnAllocate.addEventListener("click", async () => {
    const reg = regInput.value.trim().toUpperCase();
    if (!reg) {
      showAlert("Please enter or scan a valid vehicle registration number.", "warning");
      return;
    }

    const catRadio = document.querySelector('input[name="parking_category"]:checked');
    if (!catRadio) {
      showAlert("Please select a parking category.", "warning");
      return;
    }
    const category = catRadio.value;

    btnAllocate.disabled = true;
    btnAllocate.textContent = "Allocating Slot...";

    try {
      const resp = await fetch("/api/entry/create-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ registration_number: reg, parking_category: category })
      });
      const data = await resp.json();

      if (data.success) {
        // Display digital ticket
        const session = data.session;
        const slot = data.slot;

        document.getElementById("tkt-id").textContent = session.ticket_id;
        document.getElementById("tkt-reg").textContent = session.registration_number;
        document.getElementById("tkt-category").textContent = session.parking_category;
        document.getElementById("tkt-slot").textContent = slot.slot_number;
        document.getElementById("tkt-entry-time").textContent = new Date(session.entry_time).toLocaleString();

        ticketDisplay.style.display = "block";
        showAlert(`Success! Slot ${slot.slot_number} assigned. Ticket #${session.ticket_id} created.`, "info");

        // Refresh category availability badges
        refreshAvailability();
      } else {
        showAlert(data.error || "Slot allocation failed.", "danger");
      }
    } catch (err) {
      showAlert("Network error during slot allocation.", "danger");
    } finally {
      btnAllocate.disabled = false;
      btnAllocate.textContent = "🎟️ Confirm & Allocate Slot";
    }
  });

  // Refresh live category counters
  async function refreshAvailability() {
    try {
      const res = await fetch("/api/entry/availability");
      const d = await res.json();
      if (d.success) {
        const byCat = d.availability.by_category;
        document.getElementById("cat-avail-disabled").textContent = `${byCat["Disabled Parking"].vacant} Available`;
        document.getElementById("cat-avail-ev").textContent = `${byCat["EV Charging Parking"].vacant} Available`;
        document.getElementById("cat-avail-normal").textContent = `${byCat["Normal Parking"].vacant} Available`;
      }
    } catch (e) {}
  }

  // Periodic polling for availability
  setInterval(refreshAvailability, 4000);
});

