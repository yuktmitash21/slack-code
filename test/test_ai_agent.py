import unittest
from unittest.mock import patch, MagicMock
from ai_agent import AICodeGenerator

class TestAICodeGenerator(unittest.TestCase):

    @patch('ai_agent.openai.OpenAI')
    def setUp(self, mock_openai):
        self.mock_openai = mock_openai
        self.mock_openai.return_value = MagicMock()
        self.generator = AICodeGenerator(llm_provider="openai", model_name="gpt-4o")

    def test_initialization(self):
        """Test that the AI code generator initializes correctly."""
        self.assertEqual(self.generator.llm_provider, "openai")
        self.assertEqual(self.generator.model_name, "gpt-4o")

    @patch('ai_agent.openai.OpenAI')
    def test_generate_code_for_task_success(self, mock_openai):
        """Test successful code generation."""
        mock_openai().chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="📄 File: example.py [NEW]\n