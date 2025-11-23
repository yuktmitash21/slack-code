import unittest
from unittest.mock import patch, MagicMock
from ai_agent import AICodeGenerator

class TestAICodeGenerator(unittest.TestCase):

    @patch('ai_agent.openai.OpenAI')
    def test_generate_code_for_task_success(self, MockOpenAI):
        # Mock the OpenAI response
        mock_response = MagicMock()
\n