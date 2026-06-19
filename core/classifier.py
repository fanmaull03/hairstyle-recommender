import numpy as np

class FaceShapeClassifier:
    # Label resmi + metadata
    SHAPES = {
        "oval": {"label": "Oval", "emoji": "🥚", "color": "#639922"},
        "round": {"label": "Round", "emoji": "⭕", "color": "#D85A30"},
        "square": {"label": "Square", "emoji": "🔲", "color": "#888780"},
        "heart": {"label": "Heart", "emoji": "🫀", "color": "#D4537E"},
        "oblong": {"label": "Oblong", "emoji": "📏", "color": "#378ADD"},
        "diamond": {"label": "Diamond", "emoji": "💎", "color": "#BA7517"},
    }

    def __init__(self):
        # Titik pusat ideal tiap bentuk wajah berdasarkan rasio:
        # (wh_ratio, jaw_forehead, cheek_face)
        self.centers = {
            "oval": (0.820, 0.880, 0.900),
            "round": (0.950, 0.900, 0.920),
            "square": (0.850, 0.980, 0.910),
            "heart": (0.680, 0.680, 0.870),
            "oblong": (0.640, 0.850, 0.870),
            "diamond": (0.700, 0.820, 0.960),
        }

    def predict(self, features: dict) -> dict:
        """
        Klasifikasi bentuk wajah menggunakan jarak Euclidean + Softmax.
        """
        # 1. Ambil 3 fitur utama dari wajah user
        feat_vec = np.array([
            features["wh_ratio"],
            features["jaw_forehead"],
            features["cheek_face"],
        ])

        # 2. Hitung jarak fitur user ke tiap titik ideal (Euclidean Distance)
        distances = {s: np.linalg.norm(feat_vec - np.array(c)) for s, c in self.centers.items()}

        # 3. Bentuk wajah dengan jarak TERDEKAT adalah tebakan utama kita
        predicted_shape = min(distances, key=distances.get)

        # 4. Hitung Confidence Score (Softmax dengan Temperature)
        # Temperature 20.0 akan membuat tebakan terdekat melonjak persenannya
        temperature = 20.0
        exp_scores = {s: np.exp(-d * temperature) for s, d in distances.items()}
        total_exp = sum(exp_scores.values())
        
        # Ubah jadi persentase (0.0 sampai 1.0)
        scores = {s: round(v / total_exp, 3) for s, v in exp_scores.items()}
        confidence = round(scores[predicted_shape], 3)

        return {
            "shape": predicted_shape,
            "label": self.SHAPES[predicted_shape]["label"],
            "confidence": confidence,
            "scores": scores,
            "features": features,
            "reasoning": self._reasoning(predicted_shape, features),
        }

    def _reasoning(self, shape: str, features: dict) -> str:
        """Penjelasan singkat kenapa diklasifikasikan sebagai shape ini."""
        wh = features["wh_ratio"]
        jf = features["jaw_forehead"]
        cf = features["cheek_face"]

        reasons = {
            "oval": f"Rasio lebar/tinggi {wh:.2f} proporsional, rahang sedikit lebih sempit dari dahi (rasio {jf:.2f}).",
            "round": f"Rasio lebar/tinggi {wh:.2f} mendekati 1:1, wajah cenderung bulat dan pipi penuh.",
            "square": f"Rasio lebar/tinggi {wh:.2f} proporsional namun rahang hampir selebar dahi (rasio {jf:.2f}), garis rahang tegas.",
            "heart": f"Dahi lebih lebar dari rahang (rasio {jf:.2f}), wajah menyempit ke bawah menuju dagu.",
            "oblong": f"Rasio lebar/tinggi {wh:.2f} menunjukkan wajah panjang dan sempit dengan lebar yang merata.",
            "diamond": f"Tulang pipi sangat menonjol (rasio {cf:.2f}), dahi dan rahang relatif sempit.",
        }
        return reasons.get(shape, "")
