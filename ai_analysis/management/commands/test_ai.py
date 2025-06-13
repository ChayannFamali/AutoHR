from django.core.management.base import BaseCommand

from ai_analysis.services.document_parser import DocumentParser


class Command(BaseCommand):
    help = 'Test AI components'
    
    def handle(self, *args, **options):
        try:
            # Тест парсера
            parser = DocumentParser()
            self.stdout.write("✓ Document parser loaded")
            
            # Тест embedding service
            from ai_analysis.services.embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            self.stdout.write("✓ Embedding service loaded")
            
            # Тест создания embedding
            test_text = "Python developer with 3 years experience"
            embedding = embedding_service.create_text_embedding(test_text)
            if embedding:
                self.stdout.write("✓ Embedding creation works")
            else:
                self.stdout.write("✗ Embedding creation failed")
                
        except Exception as e:
            self.stdout.write(f"✗ Error: {str(e)}")
