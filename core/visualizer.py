import base64
import math

import cv2
import dlib
import numpy as np


def encode_image_to_base64(image_array):
    ret, buffer = cv2.imencode(".jpg", image_array)
    return base64.b64encode(buffer).decode("utf-8")


def get_processing_steps(
    image_path, predictor_path="models/shape_predictor_68_face_landmarks.dat"
):
    steps = {}

    img = cv2.imread(image_path)
    if img is None:
        return None

    # 1. ORIGINAL
    steps["1_original"] = encode_image_to_base64(img)

    # 2. GRAYSCALE
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    steps["2_grayscale"] = encode_image_to_base64(gray)

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    faces = detector(gray)

    if len(faces) == 0:
        return None
    face = faces[0]

    # KUNCI PERBAIKAN: Ubah grayscale kembali ke BGR (3 channel) sebagai KANVAS.
    # Gambar akan tampak hitam-putih, tapi kita bisa menggambar warna di atasnya.
    gray_canvas = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    # 3. FACE DETECTION (Di atas kanvas grayscale)
    img_bbox = gray_canvas.copy()
    cv2.rectangle(
        img_bbox,
        (face.left(), face.top()),
        (face.right(), face.bottom()),
        (0, 255, 0),  # Warna hijau akan sangat jelas di atas hitam-putih
        2,
    )
    steps["3_face_detection"] = encode_image_to_base64(img_bbox)

    # 4. LANDMARKS (Blueprint style)
    landmarks = predictor(gray, face)

    # Menggunakan kanvas grayscale, lalu sedikit digelapkan agar titik putih & kuning menyala
    img_landmarks = gray_canvas.copy()
    img_landmarks = cv2.addWeighted(
        img_landmarks, 0.4, np.zeros_like(img_landmarks), 0, 0
    )

    for n in range(0, 68):
        x, y = landmarks.part(n).x, landmarks.part(n).y
        cv2.circle(img_landmarks, (x, y), 2, (255, 255, 255), -1)

        if n % 5 == 0 or n in [1, 4, 8, 12, 15, 27]:
            cv2.putText(
                img_landmarks,
                str(n),
                (x + 3, y + 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3,
                (0, 255, 255),
                1,
            )
    steps["4_landmarks"] = encode_image_to_base64(img_landmarks)

    # 5. GEOMETRI & EUCLIDEAN (Di atas kanvas grayscale)
    img_shape = gray_canvas.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_measurement(img, p1_idx, p2_idx, color, label_text):
        p1 = (landmarks.part(p1_idx).x, landmarks.part(p1_idx).y)
        p2 = (landmarks.part(p2_idx).x, landmarks.part(p2_idx).y)
        dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])

        # Gambar garis dan titik
        cv2.line(img, p1, p2, color, 2, cv2.LINE_AA)
        cv2.circle(img, p1, 5, color, -1)
        cv2.circle(img, p2, 5, color, -1)

        # Label Titik
        cv2.putText(
            img, f"Pt.{p1_idx}", (p1[0] - 25, p1[1] - 10), font, 0.5, (255, 255, 255), 2
        )
        cv2.putText(
            img, f"Pt.{p2_idx}", (p2[0] + 5, p2[1] - 10), font, 0.5, (255, 255, 255), 2
        )

        # Hasil Ukur
        mid = (int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2) - 10)

        # Tambahkan background teks hitam kecil agar angka mudah dibaca
        text = f"{label_text}: {int(dist)}px"
        (text_w, text_h), _ = cv2.getTextSize(text, font, 0.5, 2)
        cv2.rectangle(
            img,
            (mid[0] - 2, mid[1] - text_h - 2),
            (mid[0] + text_w + 2, mid[1] + 2),
            (0, 0, 0),
            -1,
        )
        cv2.putText(img, text, mid, font, 0.5, color, 2)

    # Eksekusi Pengukuran
    draw_measurement(img_shape, 1, 15, (0, 255, 255), "Lebar (W)")  # Kuning
    draw_measurement(img_shape, 4, 12, (255, 100, 255), "Rahang (J)")  # Pink

    # Tinggi Wajah (8 ke 27)
    p8 = (landmarks.part(8).x, landmarks.part(8).y)
    p27 = (landmarks.part(27).x, landmarks.part(27).y)
    dist_half_height = math.hypot(p27[0] - p8[0], p27[1] - p8[1])
    est_dahi = (p27[0], int(p27[1] - dist_half_height))

    # Garis Tinggi
    cv2.line(img_shape, p8, est_dahi, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.circle(img_shape, p8, 5, (0, 255, 0), -1)
    cv2.circle(img_shape, p27, 5, (0, 255, 0), -1)
    cv2.circle(img_shape, est_dahi, 5, (0, 255, 0), -1)

    cv2.putText(
        img_shape, "Pt.8", (p8[0] + 10, p8[1] + 15), font, 0.5, (255, 255, 255), 2
    )
    cv2.putText(
        img_shape, "Pt.27", (p27[0] + 10, p27[1]), font, 0.5, (255, 255, 255), 2
    )
    cv2.putText(
        img_shape,
        "Est. Dahi",
        (est_dahi[0] + 10, est_dahi[1]),
        font,
        0.5,
        (255, 255, 255),
        2,
    )

    mid_h = (p27[0] + 15, int((p8[1] + est_dahi[1]) / 2))

    # Label tinggi dengan background hitam agar terbaca
    text_h_str = f"Tinggi (H): {int(dist_half_height * 2)}px"
    (tw, th), _ = cv2.getTextSize(text_h_str, font, 0.5, 2)
    cv2.rectangle(
        img_shape,
        (mid_h[0] - 2, mid_h[1] - th - 2),
        (mid_h[0] + tw + 2, mid_h[1] + 2),
        (0, 0, 0),
        -1,
    )
    cv2.putText(img_shape, text_h_str, mid_h, font, 0.5, (0, 255, 0), 2)

    steps["5_shape_pattern"] = encode_image_to_base64(img_shape)

    return steps
