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
from core.visualizer import get_processing_steps

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

        /* CSS untuk Referensi Bentuk Wajah */
        .shape-ref {
            width: 80px;
            height: 100px;
            border: 3px dashed #10b981;
            margin: 0 auto;
        }
        .shape-oval { border-radius: 50% / 60% 60% 40% 40%; }
        .shape-round { border-radius: 50%; width: 90px; height: 90px; }
        .shape-square { border-radius: 15%; width: 90px; height: 90px; }
        .shape-oblong { border-radius: 40px; height: 110px; width: 70px; }
        .shape-diamond { transform: rotate(45deg); width: 70px; height: 70px; margin: 15px auto; }
        .shape-heart {
            border-radius: 50% 50% 50% 50% / 30% 30% 70% 70%;
            clip-path: polygon(50% 100%, 100% 30%, 80% 0%, 50% 15%, 20% 0%, 0 30%);
            background: transparent;
            border: 3px dashed #10b981;
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
                        <div class="mb-6 flex items-center justify-center lg:justify-start gap-6">
                            <div class="text-center lg:text-left">
                                <span class="inline-block px-3 py-1 bg-white border border-slate-200 rounded-full text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 shadow-sm">
                                    Bentuk Wajah Terdeteksi
                                </span>
                                <p class="text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-brand-500 to-blue-700 capitalize">
                                    {{ result.label }}
                                </p>
                            </div>

                            <div class="bg-white p-3 rounded-xl border border-slate-200 shadow-inner flex flex-col items-center justify-center min-w-[100px] hidden md:flex">
                                <div class="shape-ref shape-{{ result.label | lower }}"></div>
                                <span class="text-[10px] text-slate-400 font-bold uppercase mt-2 tracking-widest">Pola Asli</span>
                            </div>
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

               {% if steps %}
                               <div class="mt-8 mb-10 pt-8 border-t border-slate-200">
                                   <div class="text-center mb-6">
                                       <h3 class="text-lg md:text-xl font-bold text-slate-900 flex justify-center items-center gap-2">
                                           <i class="fa-solid fa-microchip text-brand-500"></i> Tahapan Pemrosesan Citra Digital
                                       </h3>
                                       <p class="text-sm text-slate-500 mt-1">Bagaimana AI melihat dan memetakan wajahmu</p>
                                   </div>

                                   <div class="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                                       <div class="flex flex-col items-center bg-slate-50 p-2 rounded-xl border border-slate-200">
                                           <span class="text-xs font-semibold text-slate-600 mb-2">1. Original</span>
                                           <img src="data:image/jpeg;base64,{{ steps['1_original'] }}" class="rounded-lg shadow-sm border border-slate-200 w-full object-cover">
                                       </div>
                                       <div class="flex flex-col items-center bg-slate-50 p-2 rounded-xl border border-slate-200">
                                           <span class="text-xs font-semibold text-slate-600 mb-2">2. Grayscale</span>
                                           <img src="data:image/jpeg;base64,{{ steps['2_grayscale'] }}" class="rounded-lg shadow-sm border border-slate-200 w-full object-cover">
                                       </div>
                                       <div class="flex flex-col items-center bg-slate-50 p-2 rounded-xl border border-slate-200">
                                           <span class="text-xs font-semibold text-slate-600 mb-2">3. Smoothing (Blur)</span>
                                           <img src="data:image/jpeg;base64,{{ steps['3_smoothing'] }}" class="rounded-lg shadow-sm border border-slate-200 w-full object-cover">
                                       </div>
                                       <div class="flex flex-col items-center bg-slate-50 p-2 rounded-xl border border-slate-200">
                                           <span class="text-xs font-semibold text-slate-600 mb-2">4. CLAHE (Kontras)</span>
                                           <img src="data:image/jpeg;base64,{{ steps['4_clahe_enhancement'] }}" class="rounded-lg shadow-sm border border-slate-200 w-full object-cover">
                                       </div>
                                       <div class="flex flex-col items-center bg-slate-50 p-2 rounded-xl border border-slate-200">
                                           <span class="text-xs font-semibold text-slate-600 mb-2">5. Edge Detection</span>
                                           <img src="data:image/jpeg;base64,{{ steps['5_edge_detection'] }}" class="rounded-lg shadow-sm border border-slate-200 w-full object-cover">
                                       </div>
                                       <div class="flex flex-col items-center bg-slate-50 p-2 rounded-xl border border-slate-200">
                                           <span class="text-xs font-semibold text-slate-600 mb-2">6. Deteksi Wajah</span>
                                           <img src="data:image/jpeg;base64,{{ steps['6_face_detection'] }}" class="rounded-lg shadow-sm border border-slate-200 w-full object-cover">
                                       </div>
                                       <div class="flex flex-col items-center bg-slate-50 p-2 rounded-xl border border-slate-200">
                                           <span class="text-xs font-semibold text-slate-600 mb-2">7. 68 Titik Landmarks</span>
                                           <img src="data:image/jpeg;base64,{{ steps['7_landmarks'] }}" class="rounded-lg shadow-sm border border-slate-200 w-full object-cover">
                                       </div>
                                       <div class="flex flex-col items-center bg-brand-50 p-2 rounded-xl border border-brand-200">
                                           <span class="text-xs font-bold text-brand-700 mb-2">8. Pola Geometri</span>
                                           <img src="data:image/jpeg;base64,{{ steps['8_shape_pattern'] }}" class="rounded-lg shadow-sm border border-brand-200 w-full object-cover">
                                       </div>
                                   </div>
                               </div>
                               {% endif %}

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
                        <div class="bg-slate-100 rounded-2xl p-2 border border-slate-200 flex-grow flex items-center justify-center min-h-[300px] overflow-hidden group relative">
                            <img id="js-annotated" src="" alt="Annotasi Realtime" class="max-h-[450px] w-auto rounded-xl shadow-sm object-contain hidden group-hover:scale-105 transition-transform duration-500">
                        </div>
                    </div>
                </div>
                <div id="js-steps-container" class="mt-8 mb-10 pt-8 border-t border-slate-200 hidden">
                                    <div class="text-center mb-6">
                                        <h3 class="text-lg md:text-xl font-bold text-slate-900 flex justify-center items-center gap-2">
                                            <i class="fa-solid fa-microchip text-emerald-500"></i> Tahapan Pemrosesan Citra Digital
                                        </h3>
                                        <p class="text-sm text-slate-500 mt-1">Bagaimana AI melihat dan memetakan wajahmu</p>
                                    </div>

                                    <div id="js-steps-grid" class="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
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
    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    result_data = None
    img_steps = None

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
                img_steps = get_processing_steps(upload_path)

    return render_template_string(
        HTML_TEMPLATE, result=result_data, steps=img_steps, timestamp=int(time.time())
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

        result["steps"] = get_processing_steps(upload_path)
        result["timestamp"] = int(time.time())

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False)
