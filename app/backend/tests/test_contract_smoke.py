"""
Lightweight API contract tests that avoid external network calls.
Run with: python -m unittest tests.test_contract_smoke
"""
import unittest
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import ChatRequest
from services import agent_service


class ChatContractSmokeTest(unittest.TestCase):
    def test_chat_response_standard_contract(self):
        with patch.object(agent_service, "get_pubchem", return_value={
            "compound": "verubecestat",
            "name": "verubecestat",
            "formula": "C17H17F2N5O3S",
            "weight": 409.4,
            "molecular_weight": 409.4,
            "smiles": "C",
            "logp": 0.6,
            "tpsa": 126,
            "hbd": 2,
            "hba": 7,
            "rotatable_bonds": 3,
            "lipinski_pass": True,
        }), patch.object(agent_service, "get_pubmed", return_value=["12345"]), patch.object(
            agent_service, "search_pdb", return_value=[]
        ), patch.object(agent_service, "fetch_pubmed_abstracts", return_value=[]), patch.object(
            agent_service, "create_vector_database", return_value=True
        ), patch.object(agent_service, "search_vector_database", return_value=[{
            "title": "Example paper",
            "abstract": "BACE1 inhibitor research for Alzheimer disease.",
            "similarity_score": 0.9,
            "publication_date": "2025-01-01",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
            "pubmed_id": "12345",
        }]), patch.object(agent_service, "groq_client", None), patch.object(
            agent_service, "gemini_client", None
        ):
            response = agent_service.process_chat_request(
                ChatRequest(message="Find BACE1 inhibitors for Alzheimer disease")
            )
            payload = response.model_dump()

        self.assertEqual(payload["status"], "success")
        self.assertIn("chat", payload)
        self.assertIsInstance(payload["molecules"], list)
        self.assertIsInstance(payload["papers_graph"], dict)
        self.assertIsInstance(payload["rag_results"], list)
        self.assertIsInstance(payload["tools"], list)


if __name__ == "__main__":
    unittest.main()
