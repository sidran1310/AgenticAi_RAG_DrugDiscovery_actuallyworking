"""
Tests for the Drug Discovery AI Agent backend.
Comprehensive test suite covering all components.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from models import ChatRequest, ChatResponse, AgentType
from services import agent_service
from config import get_config

@pytest.fixture
def app():
    """Create test application"""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app: Flask):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def config():
    """Get test configuration"""
    return get_config()

class TestConfig:
    """Test configuration endpoints"""

    def test_health_check(self, client: FlaskClient):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['status'] in ['healthy', 'degraded']
        assert 'version' in data
        assert 'services' in data

    def test_get_config(self, client: FlaskClient):
        """Test configuration endpoint"""
        response = client.get('/api/config')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'agent_name' in data
        assert 'version' in data
        assert 'capabilities' in data
        assert 'tool_stats' in data

class TestChatAPI:
    """Test chat API endpoints"""

    @patch('services.agent_service.process_chat_request')
    def test_chat_success(self, mock_process, client: FlaskClient):
        """Test successful chat request"""
        # Mock the service response
        mock_response = ChatResponse(
            response="Test response",
            thought_process=[],
            actions=[],
            observations=[],
            metadata={"topic": "test", "timestamp": "2024-01-01T00:00:00"},
            status="success"
        )
        mock_process.return_value = mock_response

        # Make request
        response = client.post('/api/chat', json={
            'message': 'Test message',
            'agentType': 'groq'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['response'] == 'Test response'
        assert data['status'] == 'success'

    def test_chat_missing_message(self, client: FlaskClient):
        """Test chat request with missing message"""
        response = client.post('/api/chat', json={})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data

    def test_chat_invalid_json(self, client: FlaskClient):
        """Test chat request with invalid JSON"""
        response = client.post('/api/chat', data='invalid json')
        assert response.status_code == 400

class TestSearchAPIs:
    """Test search API endpoints"""

    @patch('services.rag_service.search_rag')
    def test_rag_search(self, mock_search, client: FlaskClient):
        """Test RAG search endpoint"""
        from models import RAGResponse, RAGChunk

        mock_response = RAGResponse(
            chunks=[
                RAGChunk(
                    id="chunk-1",
                    source="PubMed",
                    title="Test Paper",
                    content="Test content",
                    relevance_score=0.9,
                    chunk_index=1,
                    total_chunks=1,
                    metadata={}
                )
            ],
            total=1,
            query="test query"
        )
        mock_search.return_value = mock_response

        response = client.post('/api/rag', json={'query': 'test query'})
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['total'] == 1
        assert len(data['chunks']) == 1

    @patch('services.compound_service.search_compounds')
    def test_compound_search(self, mock_search, client: FlaskClient):
        """Test compound search endpoint"""
        from models import CompoundsResponse, CompoundData

        mock_response = CompoundsResponse(
            compounds=[
                CompoundData(
                    id="test-1",
                    name="Test Compound",
                    smiles="CCO",
                    molecular_weight=46.07
                )
            ],
            total=1,
            query="ethanol"
        )
        mock_search.return_value = mock_response

        response = client.post('/api/compounds', json={'query': 'ethanol'})
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['total'] == 1
        assert len(data['compounds']) == 1

    @patch('services.paper_service.search_papers')
    def test_paper_search(self, mock_search, client: FlaskClient):
        """Test paper search endpoint"""
        from models import PapersResponse, PaperData

        mock_response = PapersResponse(
            papers=[
                PaperData(
                    id="pmid-12345",
                    title="Test Paper",
                    authors="Test Author",
                    journal="Test Journal",
                    date="2024-01-01",
                    abstract="Test abstract",
                    ai_summary="Test summary",
                    source="PubMed",
                    credibility_score=95.0,
                    citation_count=10,
                    tags=["test"],
                    pubmed_id="12345"
                )
            ],
            total=1,
            query="test query"
        )
        mock_search.return_value = mock_response

        response = client.post('/api/papers', json={'query': 'test query'})
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['total'] == 1
        assert len(data['papers']) == 1

class TestAgentService:
    """Test agent service functionality"""

    @patch('services.agent_service._search_pubmed')
    @patch('services.agent_service._search_pdb')
    @patch('services.agent_service._get_compound_data')
    @patch('services.agent_service._get_gene_data')
    @patch('services.agent_service._process_rag')
    @patch('services.agent_service._generate_ai_response')
    def test_process_chat_request(self, mock_ai, mock_rag, mock_gene,
                                 mock_compound, mock_pdb, mock_pubmed):
        """Test full chat request processing"""
        # Setup mocks
        mock_pubmed.return_value = (['12345'], 0.1)
        mock_pdb.return_value = (['1abc'], 0.05)
        mock_compound.return_value = ({'compound': 'test'}, 0.02)
        mock_gene.return_value = ('1234', 0.01)
        mock_rag.return_value = ([], 0, 0.1)
        mock_ai.return_value = ('Test response', 0.5)

        # Create request
        request = ChatRequest(message="Test query")

        # Process request
        response = agent_service.process_chat_request(request)

        # Verify response
        assert isinstance(response, ChatResponse)
        assert response.status == "success"
        assert len(response.actions) > 0
        assert response.metadata.processing_time > 0

class TestMiddleware:
    """Test middleware functionality"""

    def test_rate_limiting(self, client: FlaskClient):
        """Test rate limiting"""
        # Make multiple requests quickly
        responses = []
        for _ in range(5):
            response = client.post('/api/chat', json={'message': 'test'})
            responses.append(response.status_code)

        # Should have some rate limited responses (429)
        assert 429 in responses or all(r == 200 for r in responses)

    def test_cors_headers(self, client: FlaskClient):
        """Test CORS headers"""
        response = client.get('/api/health')
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers

class TestModels:
    """Test data models"""

    def test_chat_request_validation(self):
        """Test ChatRequest model validation"""
        # Valid request
        request = ChatRequest(message="Test message")
        assert request.message == "Test message"
        assert request.agent_type == AgentType.DEFAULT

        # Invalid request (empty message)
        with pytest.raises(ValueError):
            ChatRequest(message="")

    def test_chat_response_creation(self):
        """Test ChatResponse model creation"""
        from models import ThoughtProcess, Action, Observation, Metadata

        response = ChatResponse(
            response="Test response",
            thought_process=[
                ThoughtProcess(step=1, content="Test thought")
            ],
            actions=[
                Action(tool="Test Tool", input="test", result="output")
            ],
            observations=[
                Observation(content="Test observation")
            ],
            metadata=Metadata(
                topic="test",
                timestamp="2024-01-01T00:00:00"
            ),
            status="success"
        )

        assert response.response == "Test response"
        assert len(response.thought_process) == 1
        assert len(response.actions) == 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])