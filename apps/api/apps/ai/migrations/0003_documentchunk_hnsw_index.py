"""
Add HNSW index on DocumentChunk embedding field.

Django's makemigrations doesn't automatically detect HnswIndex from abstract
model Meta classes, so this migration adds it manually.

HNSW (Hierarchical Navigable Small World) provides fast approximate nearest
neighbor search with good recall. Parameters:
- m=16: Connections per node (higher = better recall, more memory)
- ef_construction=64: Build quality (higher = better index, slower build)
- vector_cosine_ops: Use cosine distance for similarity
"""

from django.db import migrations
import pgvector.django


class Migration(migrations.Migration):
    dependencies = [
        ("ai", "0002_vector_extension"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="documentchunk",
            index=pgvector.django.HnswIndex(
                name="ai_documentchunk_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ),
    ]
