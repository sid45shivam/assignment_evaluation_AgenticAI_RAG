"""
Comprehensive Automated Test Suite for RAG Pipeline.

Tests:
1. Multi-format Document Loading (.md, .txt, .pdf)
2. Overlapping Chunk Generation & Boundary Awareness
3. Local Sentence-Transformers / ONNX Embedding Function
4. ChromaDB Ingestion & Persistence
5. Semantic Retrieval Accuracy & Top-K Ordering
6. Source & Page Attribution Verification
7. Rubric Evaluation Context Integration & Guardrail Enforcement
8. Unavailable Context Flagging
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rag_pipeline import (
    RAGPipeline,
    chunk_documents,
    get_embedding_function,
    load_document,
    load_reference_materials,
    split_text_overlapping,
)


class TestRAGPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.test_db_dir = cls.temp_dir.name
        cls.ref_dir = Path("tests/fixtures/reference_materials")

        cls.pipeline = RAGPipeline(
            persist_directory=cls.test_db_dir,
            collection_name="test_reference_collection"
        )

    @classmethod
    def tearDownClass(cls):
        try:
            cls.temp_dir.cleanup()
        except Exception:
            pass

    def test_01_reference_materials_exist(self):
        """Verify that MD, TXT, and PDF reference files exist."""
        self.assertTrue(self.ref_dir.exists(), "Reference materials folder does not exist")
        md_file = self.ref_dir / "lecture_notes_distribution_networks.md"
        txt_file = self.ref_dir / "inventory_theory_handout.txt"
        pdf_file = self.ref_dir / "supply_chain_strategy_reference.pdf"

        self.assertTrue(md_file.is_file(), "lecture_notes_distribution_networks.md missing")
        self.assertTrue(txt_file.is_file(), "inventory_theory_handout.txt missing")
        self.assertTrue(pdf_file.is_file(), "supply_chain_strategy_reference.pdf missing")

    def test_02_load_markdown_and_text(self):
        """Verify text extraction from Markdown and TXT files."""
        md_file = self.ref_dir / "lecture_notes_distribution_networks.md"
        md_docs = load_document(md_file)
        self.assertEqual(len(md_docs), 1)
        self.assertEqual(md_docs[0]["source"], "lecture_notes_distribution_networks.md")
        self.assertEqual(md_docs[0]["page"], 1)
        self.assertIn("Network Responsiveness", md_docs[0]["text"])

        txt_file = self.ref_dir / "inventory_theory_handout.txt"
        txt_docs = load_document(txt_file)
        self.assertEqual(len(txt_docs), 1)
        self.assertEqual(txt_docs[0]["source"], "inventory_theory_handout.txt")
        self.assertIn("EOQ", txt_docs[0]["text"])

    def test_03_load_pdf_with_pages(self):
        """Verify multi-page PDF loading and page number tracking."""
        pdf_file = self.ref_dir / "supply_chain_strategy_reference.pdf"
        pdf_docs = load_document(pdf_file)
        self.assertGreaterEqual(len(pdf_docs), 2, "PDF should have at least 2 distinct pages")

        page1 = pdf_docs[0]
        page2 = pdf_docs[1]

        self.assertEqual(page1["page"], 1)
        self.assertEqual(page2["page"], 2)
        self.assertEqual(page1["source"], "supply_chain_strategy_reference.pdf")
        self.assertIn("PART 1", page1["text"])
        self.assertIn("PART 2", page2["text"])

    def test_04_split_text_overlapping(self):
        """Verify overlapping chunk generation."""
        sample_text = (
            "Paragraph one introduces supply chain strategy. " * 8
            + "\n\n"
            + "Paragraph two covers inventory carrying cost formulas. " * 8
            + "\n\n"
            + "Paragraph three reviews distribution network design trade-offs. " * 8
        )
        chunks = split_text_overlapping(sample_text, chunk_size=300, chunk_overlap=80)
        self.assertGreater(len(chunks), 1, "Should create multiple chunks")

        # Verify non-trivial length
        for chunk in chunks:
            self.assertGreater(len(chunk), 20)

    def test_05_chunk_documents_metadata(self):
        """Verify metadata attached to chunks."""
        docs = [
            {"text": "Sample text for chunking test.", "source": "test.txt", "page": 1, "file_path": "Data/test.txt"}
        ]
        chunks = chunk_documents(docs, chunk_size=50, chunk_overlap=10)
        self.assertGreaterEqual(len(chunks), 1)
        meta = chunks[0]["metadata"]
        self.assertEqual(meta["source"], "test.txt")
        self.assertEqual(meta["page"], 1)
        self.assertEqual(meta["chunk_index"], 1)

    def test_06_embedding_function(self):
        """Verify local embedding function computes 384-dimensional dense vectors."""
        emb_fn = get_embedding_function()
        vectors = emb_fn(["Economic Order Quantity"])
        self.assertEqual(len(vectors), 1)
        self.assertEqual(len(vectors[0]), 384)

    def test_07_chromadb_ingestion(self):
        """Verify ingestion into ChromaDB."""
        summary = self.pipeline.ingest_directory(str(self.ref_dir))
        self.assertEqual(summary["status"], "SUCCESS")
        self.assertGreaterEqual(summary["chunks_ingested"], 10)
        self.assertIn("inventory_theory_handout.txt", summary["files"])
        self.assertIn("lecture_notes_distribution_networks.md", summary["files"])
        self.assertIn("supply_chain_strategy_reference.pdf", summary["files"])
        self.assertGreaterEqual(self.pipeline.collection.count(), 10)

    def test_08_retrieval_eoq_query(self):
        """Verify retrieval for EOQ Question (Question 2)."""
        results = self.pipeline.retrieve("calculate EOQ annual holding cost annual ordering cost", top_k=3)
        self.assertGreaterEqual(len(results), 1)

        top_result = results[0]
        self.assertEqual(top_result["source"], "inventory_theory_handout.txt")
        self.assertIn("Holding", top_result["content"])
        self.assertIsNotNone(top_result.get("similarity_score"))
        self.assertEqual(top_result["page"], 1)

    def test_09_retrieval_responsiveness_query(self):
        """Verify retrieval for Distribution Network Design (Question 1)."""
        results = self.pipeline.retrieve("trade-off between responsiveness and cost warehouse scaling", top_k=3)
        self.assertGreaterEqual(len(results), 1)

        sources = [r["source"] for r in results]
        self.assertTrue(
            "lecture_notes_distribution_networks.md" in sources
            or "supply_chain_strategy_reference.pdf" in sources
        )

    def test_10_retrieval_hybrid_network_page2(self):
        """Verify retrieval for Hybrid Network case (Question 3) attributes Page 2 of PDF."""
        results = self.pipeline.retrieve("hybrid hub and spoke architecture slow moving items central", top_k=3)
        self.assertGreaterEqual(len(results), 1)

        pdf_page2_hits = [
            r for r in results
            if r["source"] == "supply_chain_strategy_reference.pdf" and r["page"] == 2
        ]
        self.assertGreaterEqual(len(pdf_page2_hits), 1, "Should retrieve chunk from Page 2 of PDF")

    def test_11_rubric_evaluation_integration_and_guardrails(self):
        """Verify retrieve_for_rubric_evaluation and prompt formatting with guardrails."""
        eval_context = self.pipeline.retrieve_for_rubric_evaluation(
            question_title="Question 2: EOQ Calculation",
            criterion_text="Criterion 2: EOQ Result approximately 707 units",
            top_k=3
        )
        self.assertEqual(eval_context["status"], "AVAILABLE")
        self.assertGreaterEqual(len(eval_context["chunks"]), 1)

        formatted_text = self.pipeline.format_context_for_prompt(eval_context["chunks"])
        self.assertIn("Supporting Evidence Only", formatted_text)
        self.assertIn("approved rubric remains the primary scoring authority", formatted_text)
        self.assertIn("Source:", formatted_text)
        self.assertIn("Page:", formatted_text)

    def test_12_unavailable_context_flagging(self):
        """Verify unavailable context flagging on empty collection."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as empty_dir:
            empty_pipeline = RAGPipeline(
                persist_directory=empty_dir,
                collection_name="empty_test_collection"
            )
            eval_context = empty_pipeline.retrieve_for_rubric_evaluation(
                question_title="Quantum Physics",
                criterion_text="Schrodinger Wave Equation",
                top_k=3
            )
            self.assertEqual(eval_context["status"], "UNAVAILABLE")
            self.assertIn("strictly against approved rubric", eval_context["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
