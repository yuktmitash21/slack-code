import unittest
from unittest.mock import patch, MagicMock
import os

from ai_agent import AICodeGenerator

class TestAICodeGenerator(unittest.TestCase):

    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "test-api-key"
        self.generator = AICodeGenerator()

    def tearDown(self):
        del os.environ["OPENAI_API_KEY"]

    @patch('ai_agent.openai.OpenAI')
    def test_generate_code_for_task_success(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="response content"))]
        mock_client.chat.completions.create.return_value = mock_response

        result = self.generator.generate_code_sync("Test task", "Test context")
        self.assertTrue(result['success'])
        self.assertIn('files', result)
        self.assertIn('raw_response', result)

    @patch('ai_agent.openai.OpenAI')
    def test_generate_code_for_task_no_api_key(self, mock_openai):
        del os.environ["OPENAI_API_KEY"]

        with self.assertRaises(ValueError) as context:
            AICodeGenerator()
        self.assertEqual(str(context.exception), "OPENAI_API_KEY required for code generation")

    @patch('ai_agent.openai.OpenAI')
    def test_generate_code_for_task_exception(self, mock_openai):
        mock_openai.side_effect = Exception("API Error")

        result = self.generator.generate_code_sync("Test task", "Test context")
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "API Error")
        self.assertEqual(len(result['files']), 0)

    def test_parse_agent_response_valid_response(self):
        response_text = """