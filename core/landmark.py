import dlib
import cv2
import numpy as np

class LandmarkDetector:
    def __init__(self, model_path="models/shape_predictor_68_face_landmarks.dat"):
        self.detector  = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(model_path)

    def detect(self, gray_img, bbox, debug=False):
        # Pastikan gambar 8-bit grayscale
        if gray_img.dtype != np.uint8:
            gray_img = gray_img.astype(np.uint8)
        
        # Kalau ternyata masih BGR/RGB, konversi ke grayscale
        if len(gray_img.shape) == 3:
            gray_img = cv2.cvtColor(gray_img, cv2.COLOR_BGR2GRAY)

        x, y, w, h = bbox
        rect   = dlib.rectangle(x, y, x + w, y + h)
        shape  = self.predictor(gray_img, rect)
        points = self._shape_to_array(shape)

        if debug:
            return {
                "points"  : points,
                "annotated": self._draw(gray_img.copy(), points),
            }
        return points

    def extract_features(self, points):
        """
        Hitung fitur geometri dari 68 landmark.
        Indeks Dlib mulai dari 0, jadi titik ke-N = points[N-1].

        Return: dict fitur yang dipakai classifier.
        """
        # ── Lebar & tinggi wajah ──────────────────────────────
        # Titik 1 (kiri) ↔ 17 (kanan) = lebar maksimum wajah
        face_width  = self._dist(points[0],  points[16])

        # Titik 8 (dagu) ↔ 28 (pangkal hidung/dahi bawah)
        # Kita estimasi tinggi dari dagu ke dahi atas (titik 20 area dahi)
        face_height = self._dist(points[8],  points[19])

        # ── Lebar rahang ──────────────────────────────────────
        # Titik 5 ↔ 13 (area mandibula, lebih ke bawah dari pipi)
        jaw_width   = self._dist(points[4],  points[12])

        # ── Lebar dahi ────────────────────────────────────────
        # Titik 18 ↔ 27 (ujung alis kiri dan kanan)
        forehead_width = self._dist(points[17], points[26])

        # ── Lebar pipi (cheekbone) ────────────────────────────
        # Titik 2 ↔ 16 (area pipi atas)
        cheek_width = self._dist(points[1], points[15])

        # ── Rasio utama ───────────────────────────────────────
        wh_ratio        = face_width   / face_height       if face_height   > 0 else 0
        jaw_forehead    = jaw_width    / forehead_width     if forehead_width > 0 else 0
        cheek_face      = cheek_width  / face_width         if face_width    > 0 else 0

        return {
            "face_width"      : round(float(face_width),    2),
            "face_height"     : round(float(face_height),   2),
            "jaw_width"       : round(float(jaw_width),     2),
            "forehead_width"  : round(float(forehead_width),2),
            "cheek_width"     : round(float(cheek_width),   2),
            "wh_ratio"        : round(float(wh_ratio),      4),
            "jaw_forehead"    : round(float(jaw_forehead),  4),
            "cheek_face"      : round(float(cheek_face),    4),
        }

    def _dist(self, p1, p2):
        """Jarak Euclidean antara dua titik."""
        return np.linalg.norm(np.array(p1) - np.array(p2))

    def _shape_to_array(self, shape):
        """Konversi objek dlib shape → numpy array (68, 2)."""
        return np.array([[shape.part(i).x, shape.part(i).y]
                         for i in range(68)], dtype=np.int32)

    def _draw(self, img, points):
        """Gambar semua 68 titik + nomor di atas foto. Untuk debug."""
        # Warna per region
        colors = {
            range(0,  17): (214,  90,  48),   # jaw    — coral
            range(17, 27): (127, 119, 221),   # brow   — purple
            range(27, 36): ( 29, 158, 117),   # nose   — teal
            range(36, 48): ( 55, 138, 221),   # eyes   — blue
            range(48, 68): (186, 117,  23),   # mouth  — amber
        }
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        for r, color in colors.items():
            for i in r:
                x, y = points[i]
                cv2.circle(img, (x, y), 3, color, -1)
                cv2.putText(img, str(i+1), (x+3, y-3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.28, color, 1)
        return img