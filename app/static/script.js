// === LOGIKA UNTUK UPLOAD & PREVIEW FOTO ===
const dropzone = document.getElementById("dropzone");
const uploadForm = document.getElementById("upload-form");
const submitUploadBtn = document.getElementById("submit-upload-btn");
const dropText = document.getElementById("drop-text");
const previewContainer = document.getElementById("preview-container");
const imagePreview = document.getElementById("image-preview");

function previewImage(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function (e) {
      imagePreview.src = e.target.result;
      dropText.classList.add("hidden");
      previewContainer.classList.remove("hidden");
      dropzone.classList.remove("border-dashed");
      dropzone.classList.add("border-solid", "border-brand-400");
    };
    reader.readAsDataURL(input.files[0]);
  }
}

uploadForm.addEventListener("submit", function () {
  submitUploadBtn.disabled = true;
  submitUploadBtn.innerHTML =
    '<i class="fa-solid fa-spinner fa-spin"></i> Sedang Memproses...';
});

// === LOGIKA UNTUK KAMERA WEBCAM ===
const video = document.getElementById("webcam");
const captureBtn = document.getElementById("capture-btn");
const camStatus = document.getElementById("cam-status");
const scannerLine = document.getElementById("scanner");

const jsResultCard = document.getElementById("js-result-card");
const jsInfo = document.getElementById("js-info");
const jsAnnotated = document.getElementById("js-annotated");
const jsGrid = document.getElementById("js-hairstyle-grid");

const jsStepsContainer = document.getElementById("js-steps-container");
const jsStep1 = document.getElementById("js-step-1");
const jsStep2 = document.getElementById("js-step-2");
const jsStep3 = document.getElementById("js-step-3");
const jsStep4 = document.getElementById("js-step-4");
const jsStep5 = document.getElementById("js-step-5");

const isMobile = window.innerWidth < 768;
const videoConstraints = {
  width: isMobile ? { ideal: 480 } : { ideal: 640 },
  height: isMobile ? { ideal: 640 } : { ideal: 480 },
  facingMode: "user",
};

navigator.mediaDevices
  .getUserMedia({ video: videoConstraints })
  .then((stream) => {
    video.srcObject = stream;
    camStatus.innerHTML =
      '<span class="text-emerald-600 font-semibold"><i class="fa-solid fa-circle-check"></i> Kamera siap digunakan</span>';
  })
  .catch((err) => {
    camStatus.innerHTML = `<span class="text-red-500"><i class="fa-solid fa-circle-xmark"></i> Kamera tidak dapat diakses. Pastikan browser diizinkan mengakses kamera.</span>`;
    captureBtn.disabled = true;
  });

captureBtn.addEventListener("click", async () => {
  if (!video.videoWidth) return;

  const originalBtnText = captureBtn.innerHTML;
  captureBtn.disabled = true;
  captureBtn.innerHTML =
    '<i class="fa-solid fa-spinner fa-spin"></i> Menganalisis...';
  camStatus.innerHTML =
    '<span class="text-emerald-600"><i class="fa-solid fa-microchip fa-fade"></i> AI sedang bekerja...</span>';
  scannerLine.classList.remove("hidden");

  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.translate(canvas.width, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(video, 0, 0);

  const dataUrl = canvas.toDataURL("image/jpeg", 0.9);

  try {
    const res = await fetch("/analyze_capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataUrl }),
    });
    const result = await res.json();

    if (result.success) {
      updateResultUI(result);
      camStatus.innerHTML =
        '<span class="text-emerald-600 font-semibold"><i class="fa-solid fa-check-double"></i> Analisis berhasil!</span>';
    } else {
      showErrorUI(result.error);
    }
  } catch (e) {
    showErrorUI("Gagal terhubung ke server. Periksa koneksi internet.");
  }

  captureBtn.disabled = false;
  captureBtn.innerHTML = originalBtnText;
  scannerLine.classList.add("hidden");
});

function showErrorUI(message) {
  camStatus.innerHTML = `<span class="text-red-500 font-semibold"><i class="fa-solid fa-triangle-exclamation"></i> Gagal: ${message}</span>`;
  alert("Terjadi Kesalahan: " + message);
}

function updateResultUI(result) {
  const postResult = document.getElementById("post-result-card");
  if (postResult) postResult.style.display = "none";

  jsResultCard.classList.remove("hidden");

  let featuresHTML = "";
  for (const [k, v] of Object.entries(result.features || {})) {
    featuresHTML += `
                    <li class="bg-white px-3 py-2 rounded-lg border border-slate-200 flex justify-between shadow-sm">
                        <span>${k}</span>
                        <span class="font-bold text-slate-800">${typeof v === "number" ? v.toFixed(2) : v}</span>
                    </li>`;
  }

  jsInfo.innerHTML = `
                <div class="mb-6 flex items-center justify-center lg:justify-start gap-6">
                    <div class="text-center lg:text-left">
                        <span class="inline-block px-3 py-1 bg-white border border-slate-200 rounded-full text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 shadow-sm">
                            Bentuk Wajah Terdeteksi
                        </span>
                        <p class="text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-teal-700 capitalize">
                            ${result.label}
                        </p>
                    </div>
                    <div class="bg-white p-3 rounded-xl border border-slate-200 shadow-inner flex flex-col items-center justify-center min-w-[100px] hidden md:flex">
                        <div class="shape-ref shape-${result.label.toLowerCase()}"></div>
                        <span class="text-[10px] text-slate-400 font-bold uppercase mt-2 tracking-widest">Pola Asli</span>
                    </div>
                </div>
                <div class="space-y-4 mb-6">
                    <div class="bg-white p-4 rounded-xl border border-slate-100 shadow-sm flex justify-between items-center">
                        <span class="text-slate-500 text-sm font-semibold flex items-center gap-2"><i class="fa-solid fa-radar-relative text-emerald-400"></i> Akurasi AI</span>
                        <span class="font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-3 py-1 rounded-lg text-sm">
                            ${(result.confidence * 100).toFixed(1)}%
                        </span>
                    </div>
                    <div class="bg-emerald-50 p-4 rounded-xl border border-emerald-100">
                        <span class="text-emerald-700 text-xs font-bold uppercase tracking-wider block mb-1">Catatan Analisis:</span>
                        <p class="text-sm font-medium text-slate-700 leading-relaxed">${result.reasoning}</p>
                    </div>
                </div>
                <div class="mt-auto">
                    <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <i class="fa-solid fa-ruler-combined"></i> Detail Geometri
                    </h4>
                    <ul class="grid grid-cols-2 gap-2 text-sm text-slate-600">
                        ${featuresHTML}
                    </ul>
                </div>
            `;

  jsAnnotated.src = "/data/hasil_annotasi.jpg?t=" + result.timestamp;
  jsAnnotated.classList.remove("hidden");

  if (result.steps) {
    jsStepsContainer.classList.remove("hidden");
    jsStep1.src = "data:image/jpeg;base64," + result.steps["1_original"];
    jsStep2.src = "data:image/jpeg;base64," + result.steps["2_grayscale"];
    jsStep3.src = "data:image/jpeg;base64," + result.steps["3_face_detection"];
    jsStep4.src = "data:image/jpeg;base64," + result.steps["4_landmarks"];
    jsStep5.src = "data:image/jpeg;base64," + result.steps["5_shape_pattern"];
  }

  jsGrid.innerHTML = result.hairstyles
    .map((h) => {
      const slug = h.name.toLowerCase().replace(/ /g, "_");
      return `
                    <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-xl hover:border-emerald-300 transition-all duration-300 group flex flex-col cursor-pointer">
                        <div class="aspect-[4/5] bg-slate-100 overflow-hidden relative">
                            <img src="/static/images/hairstyles/${result.face_shape}/${slug}/${slug}_1.jpg"
                                 onerror="this.onerror=null; this.src='/static/images/hairstyles/diamond/fringe/fringe_1.jpg';"
                                 alt="${h.name}"
                                 class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700">
                            <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        </div>
                        <div class="p-5 flex-grow flex flex-col justify-between bg-white z-10 relative">
                            <div>
                                <h4 class="text-lg font-bold text-slate-900 mb-2 capitalize group-hover:text-emerald-600 transition-colors">${h.name}</h4>
                                <p class="text-slate-500 text-sm leading-relaxed">${h.description}</p>
                            </div>
                        </div>
                    </div>`;
    })
    .join("");

  const yOffset = -70;
  const y =
    jsResultCard.getBoundingClientRect().top + window.pageYOffset + yOffset;
  window.scrollTo({ top: y, behavior: "smooth" });
}
