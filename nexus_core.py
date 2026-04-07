from sklearn.base import BaseEstimator, TransformerMixin
from sentence_transformers import SentenceTransformer


class TextEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, model_name='paraphrase-multilingual-mpnet-base-v2'):
        self.model_name = model_name

    def fit(self, X, y=None):
        # Initialisation lors du fit pour profiter du GPU d'entraînement
        self._get_encoder()
        return self

    def transform(self, X):
        encoder = self._get_encoder()
        return encoder.encode(
            list(X),
            show_progress_bar=False,
            batch_size=64
        )

    def _get_encoder(self):
        # Lazy init : survit au pickle sans recréer l'objet inutilement
        if not hasattr(self, '_encoder') or self._encoder is None:
            print(f"👁️ Chargement encodeur ({self.model_name})...")
            self._encoder = SentenceTransformer(self.model_name)
        return self._encoder

    def __getstate__(self):
        # Ne sérialise PAS le modèle SentenceTransformer (trop lourd)
        state = self.__dict__.copy()
        state['_encoder'] = None
        return state