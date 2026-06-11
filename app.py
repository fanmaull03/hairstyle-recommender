import base64
import os
import sys
import time

import cv2
import numpy as np
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_from_directory,
)

sys.path.insert(0, ".")
from core.recommender import HairstyleRecommender

app = Flask(__name__, static_folder="app/static")

rec = HairstyleRecommender()

UPLOAD_FOLDER = "data"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route("/data/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Hairstyle Recommender</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Inter', 'sans-serif'], },
                    colors: { brand: { 50: '#eff6ff', 500: '#3b82f6', 600: '#2563eb', 900: '#1e3a8a' } }
                }
            }
        }
    </script>
    <style>
        body { font-family: 'Inter', sans-serif; -webkit-tap-highlight-color: transparent; }
        #webcam { transform: scaleX(-1); } /* Efek cermin */

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

        /* Scanner Line Animation */
        @keyframes scan {
            0% { top: 10%; opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { top: 90%; opacity: 0; }
        }
        .scanner-line {
            position: absolute;
            width: 80%;
            height: 2px;
            background: rgba(16, 185, 129, 0.8);
            box-shadow: 0 0 8px 2px rgba(16, 185, 129, 0.4);
            left: 10%;
            animation: scan 3s infinite linear;
            z-index: 10;
        }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col selection:bg-brand-500 selection:text-white">

    <header class="bg-white/80 backdrop-blur-md shadow-sm border-b border-slate-200 sticky top-0 z-30">
        <div class="max-w-5xl mx-auto px-4 md:px-6 py-3 md:py-4 flex items-center justify-between">
            <h1 class="text-xl md:text-2xl font-bold text-slate-900 flex items-center gap-3">
                <div class="bg-gradient-to-br from-brand-500 to-blue-700 text-white p-2 rounded-xl shadow-sm flex items-center justify-center">
                    <i class="fa-solid fa-scissors text-lg md:text-xl"></i>
                </div>
                Hairstyle AI
            </h1>
        </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-10 flex-grow w-full">
        <div class="text-center mb-8 md:mb-12">
            <h2 class="text-3xl md:text-5xl font-extrabold text-slate-900 mb-3 md:mb-4 tracking-tight leading-tight">
                Temukan Gaya Rambut <br class="hidden md:block"> Paling Ideal
            </h2>
            <p class="text-slate-500 max-w-2xl mx-auto text-sm md:text-lg px-2 leading-relaxed">
                Teknologi AI kami menganalisis struktur dan proporsi wajahmu untuk merekomendasikan potongan rambut terbaik yang menonjolkan fitur aslimu.
            </p>
        </div>

        <div class="bg-white rounded-3xl shadow-sm border border-slate-200 p-5 md:p-8 mb-8 md:mb-12">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:divide-x lg:divide-y-0 divide-y divide-slate-100">

                <div class="lg:pr-8 pt-4 lg:pt-0 first:pt-0 flex flex-col">
                    <div class="flex items-center gap-3 mb-5">
                        <div class="bg-brand-50 p-3 rounded-xl text-brand-600 flex items-center justify-center">
                            <i class="fa-solid fa-cloud-arrow-up text-xl"></i>
                        </div>
                        <h3 class="text-lg md:text-xl font-bold text-slate-900">Upload Foto</h3>
                    </div>

                    <form id="upload-form" method="POST" action="/" enctype="multipart/form-data" class="flex flex-col flex-grow space-y-5">
                        <div id="dropzone" class="relative flex-grow min-h-[200px] border-2 border-dashed border-slate-300 rounded-2xl bg-slate-50 hover:bg-brand-50 hover:border-brand-400 transition-all duration-200 group overflow-hidden">

                            <input type="file" id="foto" name="foto" accept="image/jpeg, image/jpg, image/png" required
                                   class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                                   onchange="previewImage(this)">

                            <div id="drop-text" class="absolute inset-0 flex flex-col items-center justify-center text-center p-4 z-10 pointer-events-none transition-opacity">
                                <div class="w-16 h-16 mb-4 rounded-full bg-white shadow-sm border border-slate-200 flex items-center justify-center text-slate-400 group-hover:text-brand-500 group-hover:scale-110 transition-all">
                                    <i class="fa-regular fa-image text-2xl"></i>
                                </div>
                                <p class="text-sm font-semibold text-slate-700">Pilih file atau drag & drop di sini</p>
                                <p class="text-xs text-slate-400 mt-1">Mendukung JPEG, JPG, PNG</p>
                            </div>

                            <div id="preview-container" class="absolute inset-0 z-10 hidden bg-black/5 flex items-center justify-center p-2">
                                <img id="image-preview" src="#" alt="Preview" class="max-h-full max-w-full rounded-xl object-contain shadow-sm border border-slate-200 bg-white">
                                <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-2xl">
                                    <span class="bg-white/90 text-slate-800 text-sm font-semibold px-4 py-2 rounded-lg shadow-sm">Ganti Foto</span>
                                </div>
                            </div>
                        </div>

                        <button type="submit" id="submit-upload-btn" class="w-full py-3.5 md:py-4 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-semibold transition-all shadow-sm active:scale-[0.98] flex justify-center items-center gap-2 text-sm md:text-base disabled:opacity-70 disabled:cursor-not-allowed">
                            <i class="fa-solid fa-magnifying-glass"></i> Analisis Wajah
                        </button>
                    </form>
                </div>

                <div class="lg:pl-8 pt-8 lg:pt-0 flex flex-col">
                    <div class="flex items-center gap-3 mb-5">
                        <div class="bg-emerald-50 p-3 rounded-xl text-emerald-600 flex items-center justify-center">
                            <i class="fa-solid fa-camera-viewfinder text-xl"></i>
                        </div>
                        <h3 class="text-lg md:text-xl font-bold text-slate-900">Kamera Web Real-time</h3>
                    </div>

                    <div class="bg-slate-900 rounded-2xl overflow-hidden shadow-inner aspect-[4/3] mb-5 relative flex items-center justify-center flex-grow">
                        <video id="webcam" autoplay playsinline class="w-full h-full object-cover"></video>

                        <div id="video-overlay" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div class="absolute w-[60%] h-[70%] max-w-[250px] max-h-[300px]">
                                <div class="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-emerald-500 rounded-tl-xl"></div>
                                <div class="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-emerald-500 rounded-tr-xl"></div>
                                <div class="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-emerald-500 rounded-bl-xl"></div>
                                <div class="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-emerald-500 rounded-br-xl"></div>
                            </div>
                            <div class="scanner-line hidden" id="scanner"></div>
                        </div>
                    </div>

                    <button id="capture-btn" class="w-full py-3.5 md:py-4 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-semibold transition-all shadow-md flex justify-center items-center gap-2 active:scale-[0.98] disabled:opacity-70 disabled:active:scale-100 text-sm md:text-base">
                        <i class="fa-solid fa-camera"></i> Scan & Analisis
                    </button>
                    <p id="cam-status" class="text-center text-xs md:text-sm text-slate-500 mt-3 font-medium flex items-center justify-center gap-2">
                        <i class="fa-solid fa-circle-notch fa-spin text-slate-400"></i> Mengakses kamera...
                    </p>
                </div>
            </div>
        </div>

        {% if result %}
        <div id="post-result-card" class="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden mb-10 transform transition-all animate-[fadeIn_0.5s_ease-out]">
            <div class="bg-gradient-to-r from-brand-600 to-blue-800 px-6 md:px-8 py-5">
                <h2 class="text-lg md:text-xl font-bold text-white flex items-center gap-2">
                    <i class="fa-solid fa-square-poll-vertical"></i> Laporan Analisis Wajah
                </h2>
            </div>

            <div class="p-5 md:p-8">
                {% if result.success %}
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-10">

                    <div class="lg:col-span-5 bg-slate-50 p-6 rounded-2xl border border-slate-200 h-full flex flex-col">
                        <div class="mb-6 text-center lg:text-left">
                            <span class="inline-block px-3 py-1 bg-white border border-slate-200 rounded-full text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 shadow-sm">
                                Bentuk Wajah Terdeteksi
                            </span>
                            <p class="text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-brand-500 to-blue-700 capitalize">
                                {{ result.label }}
                            </p>
                        </div>

                        <div class="space-y-4 mb-6">
                            <div class="bg-white p-4 rounded-xl border border-slate-100 shadow-sm flex justify-between items-center">
                                <span class="text-slate-500 text-sm font-semibold flex items-center gap-2"><i class="fa-solid fa-radar-relative text-brand-400"></i> Akurasi AI</span>
                                <span class="font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-3 py-1 rounded-lg text-sm">
                                    {{ "%.1f"|format(result.confidence * 100) }}%
                                </span>
                            </div>
                            <div class="bg-brand-50 p-4 rounded-xl border border-brand-100">
                                <span class="text-brand-700 text-xs font-bold uppercase tracking-wider block mb-1">Catatan Analisis:</span>
                                <p class="text-sm font-medium text-slate-700 leading-relaxed">{{ result.reasoning }}</p>
                            </div>
                        </div>

                        <div class="mt-auto">
                            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                                <i class="fa-solid fa-ruler-combined"></i> Detail Geometri
                            </h4>
                            <ul class="grid grid-cols-2 gap-2 text-sm text-slate-600">
                                {% for k, v in result.features.items() %}
                                    <li class="bg-white px-3 py-2 rounded-lg border border-slate-200 flex justify-between">
                                        <span>{{ k }}</span>
                                        <span class="font-bold text-slate-800">{{ "%.2f"|format(v) if v is float else v }}</span>
                                    </li>
                                {% endfor %}
                            </ul>
                        </div>
                    </div>

                    <div class="lg:col-span-7 flex flex-col">
                        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 text-center lg:text-left flex justify-center lg:justify-start items-center gap-2">
                            <i class="fa-solid fa-user-astronaut"></i> Visualisasi Deteksi
                        </h4>
                        <div class="bg-slate-100 rounded-2xl p-2 border border-slate-200 flex-grow flex items-center justify-center min-h-[300px] overflow-hidden relative group">
                            <img src="/data/hasil_annotasi.jpg?t={{ timestamp }}" alt="Hasil Annotasi" class="max-h-[450px] w-auto rounded-xl shadow-sm object-contain group-hover:scale-105 transition-transform duration-500">
                        </div>
                    </div>
                </div>

                <div class="border-t border-slate-200 pt-8">
                    <div class="flex items-center justify-between mb-6">
                        <h3 class="text-xl md:text-2xl font-bold text-slate-900 flex items-center gap-3">
                            <div class="bg-yellow-100 text-yellow-600 p-2 rounded-xl text-lg shadow-sm border border-yellow-200">
                                <i class="fa-solid fa-wand-magic-sparkles"></i>
                            </div>
                            Top Rekomendasi Gaya Rambut
                        </h3>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {% for h in result.hairstyles %}
                            <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-xl hover:border-brand-300 transition-all duration-300 group flex flex-col cursor-pointer">
                                <div class="aspect-[4/5] bg-slate-100 overflow-hidden relative">
                                    <img src="/static/images/hairstyles/{{ result.face_shape }}/{{ h.name.lower().replace(' ', '_') }}/{{ h.name.lower().replace(' ', '_') }}_1.jpg"
                                         onerror="this.onerror=null; this.src='/static/images/hairstyles/diamond/fringe/fringe_1.jpg';"
                                         alt="{{ h.name }}"
                                         class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700">
                                    <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                                </div>
                                <div class="p-5 flex-grow flex flex-col justify-between bg-white z-10 relative">
                                    <div>
                                        <h4 class="text-lg font-bold text-slate-900 mb-2 capitalize group-hover:text-brand-600 transition-colors">{{ h.name }}</h4>
                                        <p class="text-slate-500 text-sm leading-relaxed">{{ h.description }}</p>
                                    </div>
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                </div>
                {% else %}
                <div class="bg-red-50 border border-red-200 text-red-700 p-6 rounded-2xl flex flex-col items-center justify-center text-center gap-3">
                    <div class="w-16 h-16 bg-red-100 text-red-500 rounded-full flex items-center justify-center text-3xl mb-2">
                        <i class="fa-solid fa-face-frown-open"></i>
                    </div>
                    <h3 class="font-bold text-lg">Gagal Menganalisis</h3>
                    <p class="font-medium text-red-600/80">{{ result.error }}</p>
                    <p class="text-sm text-red-500/70 mt-2">Pastikan wajah terlihat jelas, tidak terpotong, dan pencahayaan cukup.</p>
                </div>
                {% endif %}
            </div>
        </div>
        {% endif %}

        <div id="js-result-card" class="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden mb-10 hidden">
            <div class="bg-gradient-to-r from-emerald-600 to-teal-700 px-6 md:px-8 py-5">
                <h2 class="text-lg md:text-xl font-bold text-white flex items-center gap-2">
                    <i class="fa-solid fa-bolt"></i> Laporan Analisis Kamera Real-time
                </h2>
            </div>

            <div class="p-5 md:p-8">
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-10">
                    <div class="lg:col-span-5 bg-slate-50 p-6 rounded-2xl border border-slate-200 h-full flex flex-col" id="js-info">
                        </div>

                    <div class="lg:col-span-7 flex flex-col">
                        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 text-center lg:text-left flex justify-center lg:justify-start items-center gap-2">
                            <i class="fa-solid fa-user-astronaut"></i> Visualisasi Deteksi
                        </h4>
                        <div class="bg-slate-100 rounded-2xl p-2 border border-slate-200 flex-grow flex items-center justify-center min-h-[300px] overflow-hidden group">
                            <img id="js-annotated" src="" alt="Annotasi Realtime" class="max-h-[450px] w-auto rounded-xl shadow-sm object-contain hidden group-hover:scale-105 transition-transform duration-500">
                        </div>
                    </div>
                </div>

                <div class="border-t border-slate-200 pt-8">
                    <div class="flex items-center justify-between mb-6">
                        <h3 class="text-xl md:text-2xl font-bold text-slate-900 flex items-center gap-3">
                            <div class="bg-yellow-100 text-yellow-600 p-2 rounded-xl text-lg shadow-sm border border-yellow-200">
                                <i class="fa-solid fa-wand-magic-sparkles"></i>
                            </div>
                            Top Rekomendasi Gaya Rambut
                        </h3>
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6" id="js-hairstyle-grid">
                        </div>
                </div>
            </div>
        </div>

    </main>

    <footer class="bg-white border-t border-slate-200 mt-auto py-6">
        <div class="max-w-5xl mx-auto px-4 text-center text-slate-500 text-sm font-medium">
            &copy; 2026 Hairstyle Recommender System. <br class="md:hidden"> All rights reserved.
        </div>
    </footer>

    <script>
        // === LOGIKA UNTUK UPLOAD & PREVIEW FOTO ===
        const dropzone = document.getElementById('dropzone');
        const uploadForm = document.getElementById('upload-form');
        const submitUploadBtn = document.getElementById('submit-upload-btn');
        const dropText = document.getElementById('drop-text');
        const previewContainer = document.getElementById('preview-container');
        const imagePreview = document.getElementById('image-preview');

        // Fungsi menampilkan preview gambar
        function previewImage(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    dropText.classList.add('hidden');
                    previewContainer.classList.remove('hidden');
                    dropzone.classList.remove('border-dashed');
                    dropzone.classList.add('border-solid', 'border-brand-400');
                }
                reader.readAsDataURL(input.files[0]);
            }
        }

        // Efek UI Loading saat form Upload disubmit
        uploadForm.addEventListener('submit', function() {
            submitUploadBtn.disabled = true;
            submitUploadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sedang Memproses...';
        });


        // === LOGIKA UNTUK KAMERA WEBCAM ===
        const video = document.getElementById('webcam');
        const captureBtn = document.getElementById('capture-btn');
        const camStatus = document.getElementById('cam-status');
        const scannerLine = document.getElementById('scanner');

        const jsResultCard = document.getElementById('js-result-card');
        const jsInfo = document.getElementById('js-info');
        const jsAnnotated = document.getElementById('js-annotated');
        const jsGrid = document.getElementById('js-hairstyle-grid');

        // Konfigurasi resolusi kamera
        const isMobile = window.innerWidth < 768;
        const videoConstraints = {
            width: isMobile ? { ideal: 480 } : { ideal: 640 },
            height: isMobile ? { ideal: 640 } : { ideal: 480 },
            facingMode: 'user'
        };

        // Akses kamera
        navigator.mediaDevices.getUserMedia({ video: videoConstraints })
            .then(stream => {
                video.srcObject = stream;
                camStatus.innerHTML = '<span class="text-emerald-600 font-semibold"><i class="fa-solid fa-circle-check"></i> Kamera siap digunakan</span>';
            })
            .catch(err => {
                camStatus.innerHTML = `<span class="text-red-500"><i class="fa-solid fa-circle-xmark"></i> Kamera tidak dapat diakses. Pastikan browser diizinkan mengakses kamera.</span>`;
                captureBtn.disabled = true;
            });

        // Capture gambar
        captureBtn.addEventListener('click', async () => {
            if (!video.videoWidth) return;

            // Loading state
            const originalBtnText = captureBtn.innerHTML;
            captureBtn.disabled = true;
            captureBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menganalisis...';
            camStatus.innerHTML = '<span class="text-emerald-600"><i class="fa-solid fa-microchip fa-fade"></i> AI sedang bekerja...</span>';
            scannerLine.classList.remove('hidden'); // Munculkan efek scan garis

            // Ambil dari canvas (dengan efek mirror dibalik)
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.translate(canvas.width, 0);
            ctx.scale(-1, 1);
            ctx.drawImage(video, 0, 0);

            const dataUrl = canvas.toDataURL('image/jpeg', 0.90);

            try {
                const res = await fetch('/analyze_capture', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: dataUrl })
                });
                const result = await res.json();

                if (result.success) {
                    updateResultUI(result);
                    camStatus.innerHTML = '<span class="text-emerald-600 font-semibold"><i class="fa-solid fa-check-double"></i> Analisis berhasil!</span>';
                } else {
                    showErrorUI(result.error);
                }
            } catch (e) {
                showErrorUI('Gagal terhubung ke server. Periksa koneksi internet.');
            }

            // Reset state
            captureBtn.disabled = false;
            captureBtn.innerHTML = originalBtnText;
            scannerLine.classList.add('hidden');
        });

        function showErrorUI(message) {
            camStatus.innerHTML = `<span class="text-red-500 font-semibold"><i class="fa-solid fa-triangle-exclamation"></i> Gagal: ${message}</span>`;
            // Menyisipkan error UI di div info jika mau, namun alert sederhana cukup untuk fallback
            alert('Terjadi Kesalahan: ' + message);
        }

        function updateResultUI(result) {
            // Hilangkan hasil post lama
            const postResult = document.getElementById('post-result-card');
            if(postResult) postResult.style.display = 'none';

            jsResultCard.classList.remove('hidden');

            let featuresHTML = '';
            for (const [k, v] of Object.entries(result.features || {})) {
                featuresHTML += `
                    <li class="bg-white px-3 py-2 rounded-lg border border-slate-200 flex justify-between shadow-sm">
                        <span>${k}</span>
                        <span class="font-bold text-slate-800">${typeof v === 'number' ? v.toFixed(2) : v}</span>
                    </li>`;
            }

            jsInfo.innerHTML = `
                <div class="mb-6 text-center lg:text-left">
                    <span class="inline-block px-3 py-1 bg-white border border-slate-200 rounded-full text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 shadow-sm">
                        Bentuk Wajah Terdeteksi
                    </span>
                    <p class="text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-teal-700 capitalize">
                        ${result.label}
                    </p>
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

            jsAnnotated.src = '/data/hasil_annotasi.jpg?t=' + result.timestamp;
            jsAnnotated.classList.remove('hidden');

            jsGrid.innerHTML = result.hairstyles.map(h => {
                const slug = h.name.toLowerCase().replace(/ /g, '_');
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
            }).join('');

            // Scroll otomatis
            const yOffset = -70;
            const y = jsResultCard.getBoundingClientRect().top + window.pageYOffset + yOffset;
            window.scrollTo({ top: y, behavior: 'smooth' });
        }
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    result_data = None

    if request.method == "POST":
        upload_path = os.path.join(UPLOAD_FOLDER, "foto_upload_terakhir.jpeg")
        is_file_processed = False

        if "foto" in request.files:
            file = request.files["foto"]
            if file.filename != "":
                file.save(upload_path)
                is_file_processed = True

        if is_file_processed:
            result_data = rec.analyze(upload_path)
            if result_data["success"]:
                cv2.imwrite(
                    os.path.join(UPLOAD_FOLDER, "hasil_annotasi.jpg"),
                    result_data["annotated_img"],
                )

    return render_template_string(
        HTML_TEMPLATE, result=result_data, timestamp=int(time.time())
    )


@app.route("/analyze_capture", methods=["POST"])
def analyze_capture():
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"success": False, "error": "Tidak ada data gambar."})

    try:
        header, encoded = data["image"].split(",", 1)
        img_bytes = base64.b64decode(encoded)
    except Exception:
        return jsonify({"success": False, "error": "Format base64 tidak valid."})

    upload_path = os.path.join(UPLOAD_FOLDER, "kamera_capture_terakhir.jpeg")
    with open(upload_path, "wb") as f:
        f.write(img_bytes)

    result = rec.analyze(upload_path)

    if result["success"]:
        cv2.imwrite(
            os.path.join(UPLOAD_FOLDER, "hasil_annotasi.jpg"),
            result["annotated_img"],
        )
        result.pop("annotated_img", None)
        result["timestamp"] = int(time.time())

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
