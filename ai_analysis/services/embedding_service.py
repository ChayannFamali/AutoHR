import logging
import os
import pickle
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from django.conf import settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Сервис для создания векторных представлений текста"""
    
    def __init__(self, model_name: str = 'sentence-transformers/multilingual-e5-base'):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Загружает модель для создания embeddings"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            try:
                logger.info("Trying fallback model...")
                self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                logger.info("Fallback model loaded successfully")
            except Exception as fallback_e:
                logger.error(f"Failed to load fallback model: {str(fallback_e)}")
                raise
    
    def create_text_embedding(self, text: str) -> List[float]:
        """
        Создает embedding для текста
        
        Args:
            text: Входной текст
            
        Returns:
            list: Векторное представление текста
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return []
        
        try:
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]
            
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error creating text embedding: {str(e)}")
            return []
    
    def create_skills_embedding(self, skills: List[str]) -> List[float]:
        """
        Создает embedding для списка навыков
        
        Args:
            skills: Список навыков
            
        Returns:
            list: Векторное представление навыков
        """
        if not skills:
            return []
        
        skills_text = " ".join(skills)
        return self.create_text_embedding(skills_text)
    
    def create_job_requirements_embedding(self, requirements: str, skills: List[str] = None) -> List[float]:
        """
        Создает embedding для требований вакансии
        
        Args:
            requirements: Текст требований
            skills: Дополнительные навыки
            
        Returns:
            list: Векторное представление требований
        """
        combined_text = requirements
        
        if skills:
            combined_text += " " + " ".join(skills)
        
        return self.create_text_embedding(combined_text)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Вычисляет косинусное сходство между двумя embeddings
        
        Args:
            embedding1: Первый вектор
            embedding2: Второй вектор
            
        Returns:
            float: Коэффициент сходства (0-1)
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            similarity = (similarity + 1) / 2
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Находит наиболее похожие embeddings
        
        Args:
            query_embedding: Запросный вектор
            candidate_embeddings: Список кандидатов
            top_k: Количество топ результатов
            
        Returns:
            list: Список кортежей (индекс, сходство)
        """
        similarities = []
        
        for i, candidate_embedding in enumerate(candidate_embeddings):
            similarity = self.calculate_similarity(query_embedding, candidate_embedding)
            similarities.append((i, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def save_embeddings(self, embeddings: Dict, filepath: str):
        """
        Сохраняет embeddings в файл
        
        Args:
            embeddings: Словарь с embeddings
            filepath: Путь для сохранения
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                pickle.dump(embeddings, f)
            logger.info(f"Embeddings saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving embeddings: {str(e)}")
    
    def load_embeddings(self, filepath: str) -> Dict:
        """
        Загружает embeddings из файла
        
        Args:
            filepath: Путь к файлу
            
        Returns:
            dict: Словарь с embeddings
        """
        try:
            with open(filepath, 'rb') as f:
                embeddings = pickle.load(f)
            logger.info(f"Embeddings loaded from {filepath}")
            return embeddings
        except Exception as e:
            logger.error(f"Error loading embeddings: {str(e)}")
            return {}
