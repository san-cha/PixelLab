
const fileInput = document.getElementById("fileInput");
const browseButton = document.getElementById("browseButton");
const dropZone = document.getElementById("dropZone");
const uploadPrompt = document.getElementById("uploadPrompt");
const sourcePreview = document.getElementById("sourcePreview");
const sourceImage = document.getElementById("sourceImage");
const sourceFilename = document.getElementById("sourceFilename");
const sourceDimensions = document.getElementById("sourceDimensions");
const operationSelect = document.getElementById("operationSelect");
const brightnessControl = document.getElementById("brightnessControl");
const brightnessSlider = document.getElementById("brightnessSlider");
const brightnessValue = document.getElementById("brightnessValue");
const processButton = document.getElementById("processButton");
const processButtonText = document.getElementById("processButtonText");
const resetButton = document.getElementById("resetButton");
const statusMessage = document.getElementById("statusMessage");
const resultSection = document.getElementById("resultSection");
const comparisonOriginal = document.getElementById("comparisonOriginal");
const processedImage = document.getElementById("processedImage");
const resultOperation = document.getElementById("resultOperation");
const downloadButton = document.getElementById("downloadButton");

const MAX_FILE_BYTES = 8 * 1024 * 1024;
const ALLOWED_EXTENSIONS = /\.(jpg|jpeg|png)$/i;

let selectedFile = null;
let sourceUrl = null;
let processedUrl = null;
let downloadFilename = "processed_image.png";
let busy = false;

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("error", isError);
}

function clearResult() {
  if (processedUrl) {
    URL.revokeObjectURL(processedUrl);
  }

  processedUrl = null;
  resultSection.classList.add("hidden");
  processedImage.removeAttribute("src");
  comparisonOriginal.removeAttribute("src");
}

function updateControls() {
  brightnessControl.classList.toggle(
    "hidden",
    operationSelect.value !== "brightness"
  );
}

function updateButtons() {
  processButton.disabled = !selectedFile || busy;
  resetButton.disabled = !selectedFile && !busy;
  processButtonText.textContent = busy ? "Processing image..." : "Process image";
}

function resetWorkspace() {
  selectedFile = null;
  fileInput.value = "";

  if (sourceUrl) {
    URL.revokeObjectURL(sourceUrl);
  }

  sourceUrl = null;
  sourceImage.removeAttribute("src");
  sourceFilename.textContent = "";
  sourceDimensions.textContent = "";

  uploadPrompt.classList.remove("hidden");
  sourcePreview.classList.add("hidden");

  clearResult();
  updateControls();
  updateButtons();
  setStatus("Upload an image to get started.");
}

function loadFile(file) {
  if (busy) return;

  if (!file) return;

  if (!ALLOWED_EXTENSIONS.test(file.name)) {
    setStatus("Choose a JPG, JPEG, or PNG image.", true);
    return;
  }

  if (file.size === 0) {
    setStatus("The selected file is empty.", true);
    return;
  }

  if (file.size > MAX_FILE_BYTES) {
    setStatus("This image exceeds the 8 MB upload limit.", true);
    return;
  }

  const imageUrl = URL.createObjectURL(file);
  const probe = new Image();

  probe.onload = () => {
    const pixels = probe.naturalWidth * probe.naturalHeight;

    if (pixels > 25_000_000) {
      URL.revokeObjectURL(imageUrl);
      setStatus("Image dimensions are too large. Choose a smaller image.", true);
      return;
    }

    if (sourceUrl) {
      URL.revokeObjectURL(sourceUrl);
    }

    selectedFile = file;
    sourceUrl = imageUrl;

    clearResult();

    sourceImage.src = sourceUrl;
    sourceFilename.textContent = file.name;
    sourceDimensions.textContent =
      `${probe.naturalWidth} × ${probe.naturalHeight}`;

    uploadPrompt.classList.add("hidden");
    sourcePreview.classList.remove("hidden");

    updateButtons();
    setStatus("Image ready. Choose an operation and process it.");
  };

  probe.onerror = () => {
    URL.revokeObjectURL(imageUrl);
    setStatus("The selected file cannot be previewed as an image.", true);
  };

  probe.src = imageUrl;
}

browseButton.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("click", (event) => {
  if (
    event.target.closest("button") ||
    event.target.closest("img") ||
    event.target.closest(".image-caption")
  ) {
    return;
  }

  fileInput.click();
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    loadFile(fileInput.files[0]);
  }
});

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
});

dropZone.addEventListener("drop", (event) => {
  const files = event.dataTransfer.files;

  if (files.length > 0) {
    loadFile(files[0]);
  }
});

operationSelect.addEventListener("change", () => {
  updateControls();
  clearResult();
  setStatus(
    selectedFile
      ? "Operation changed. Process the image to see the new result."
      : "Upload an image to get started."
  );
});

brightnessSlider.addEventListener("input", () => {
  brightnessValue.value = `${brightnessSlider.value}%`;
  brightnessValue.textContent = `${brightnessSlider.value}%`;
  clearResult();
});

processButton.addEventListener("click", async () => {
  if (!selectedFile || busy) return;

  busy = true;
  clearResult();
  updateButtons();
  setStatus("Processing your image...");

  const formData = new FormData();
  formData.append("image", selectedFile);
  formData.append("operation", operationSelect.value);

  if (operationSelect.value === "brightness") {
    formData.append("brightness", brightnessSlider.value);
  }

  try {
    const response = await fetch("/api/process", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let message = "Processing failed. Please try again.";

      try {
        const data = await response.json();
        if (data.error) message = data.error;
      } catch {
        message = "The server returned an unexpected response.";
      }

      throw new Error(message);
    }

    const blob = await response.blob();

    if (!blob.type.startsWith("image/")) {
      throw new Error("The server did not return a valid image.");
    }

    processedUrl = URL.createObjectURL(blob);

    const originalStem = selectedFile.name.replace(/\.[^.]+$/, "");
    downloadFilename = `${originalStem}_${operationSelect.value}.png`;

    processedImage.src = processedUrl;
    comparisonOriginal.src = sourceUrl;
    resultOperation.textContent = ` / ${operationSelect.value.toUpperCase()}`;
    resultSection.classList.remove("hidden");

    setStatus("Done. Your processed image is ready to preview and download.");
    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    clearResult();
    setStatus(error.message || "Could not reach the server. Is Flask running?", true);
  } finally {
    busy = false;
    updateButtons();
  }
});

downloadButton.addEventListener("click", () => {
  if (!processedUrl) return;

  const link = document.createElement("a");
  link.href = processedUrl;
  link.download = downloadFilename;
  document.body.appendChild(link);
  link.click();
  link.remove();
});

resetButton.addEventListener("click", resetWorkspace);

updateControls();
updateButtons();
