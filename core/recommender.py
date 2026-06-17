import json, os, cv2
from core.preprocessor  import Preprocessor
from core.face_detector import FaceDetector
from core.landmark      import LandmarkDetector
from core.classifier    import FaceShapeClassifier

class HairstyleRecommender:
    def __init__(self,
                 model_path ="models/shape_predictor_68_face_landmarks.dat",
                 data_path  ="data/hairstyles.json"):

        self.prep       = Preprocessor()
        self.detector   = FaceDetector()
        self.landmark   = LandmarkDetector(model_path)
        self.classifier = FaceShapeClassifier()

        with open(data_path, encoding="utf-8") as f:
            self.hairstyles = json.load(f)

    def analyze(self, image_source, top_n=5):
        """
        Pipeline lengkap: foto → rekomendasi hairstyle.

        Return dict:
        {
            "success"      : True/False,
            "error"        : str | None,
            "face_shape"   : "oval" | ...,
            "label"        : "Oval" | ...,
            "confidence"   : 0.85,
            "reasoning"    : "...",
            "scores"       : { "oval": 0.4, ... },
            "features"     : { "wh_ratio": ..., ... },
            "hairstyles"   : [ { name, description, images, tags }, ... ],
            "annotated_img": np.ndarray (BGR),
        }
        """
        try:
            img_bgr = self.prep.load_image(image_source)
            gray_original = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            is_valid, msg = self.detector.validate_photo(gray_original)
            if not is_valid:
                return {"success": False, "error": msg}

            stages = self.prep.run(img_bgr, debug=True)
            gray = stages["denoised"]
            bbox, err = self.detector.detect(gray)
            if err:
                return {"success": False, "error": err["error"]}

            # 4. Landmark & ekstraksi fitur
            lm_result  = self.landmark.detect(gray, bbox, debug=True)
            features   = self.landmark.extract_features(lm_result["points"])

            # 5. Klasifikasi bentuk wajah
            result     = self.classifier.predict(features)

            # 6. Ambil rekomendasi hairstyle
            shape      = result["shape"]
            hairstyles = self._get_recommendations(shape, top_n)

            # 7. Foto annotated (landmark + bbox)
            annotated  = self.detector.draw_bbox(
                             lm_result["annotated"], bbox)

            return {
                "success"      : True,
                "error"        : None,
                "face_shape"   : shape,
                "label"        : result["label"],
                "confidence"   : result["confidence"],
                "reasoning"    : result["reasoning"],
                "scores"       : result["scores"],
                "features"     : features,
                "hairstyles"   : hairstyles,
                "annotated_img": annotated,
            }

        except Exception as e:
            return {"success": False, "error": f"Terjadi kesalahan: {str(e)}"}

    def _get_recommendations(self, shape: str, top_n: int):
        """Ambil top N hairstyle dari JSON database."""
        all_styles = self.hairstyles.get(shape, [])
        return all_styles[:top_n]