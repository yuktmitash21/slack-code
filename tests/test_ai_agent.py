import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from ai_agent import AICodeGenerator, get_ai_code_generator

class TestAICodeGenerator(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        # Ensure OPENAI_API_KEY is set for tests
        self.openai_key = "test_openai_api_key"
        os.environ["OPENAI_API_KEY"] = self.openai_key

    @patch('ai_agent.openai.OpenAI')
    def test_initialization_success(self, MockOpenAI):
        """Test successful initialization of AICodeGenerator."""
        generator = AICodeGenerator(llm_provider="openai", model_name="gpt-4o")
        self.assertEqual(generator.llm_provider, "openai")
        self.assertEqual(generator.model_name, "gpt-4o")

    @patch('ai_agent.openai.OpenAI')
    def test_initialization_no_api_key(self, MockOpenAI):
        """Test initialization failure without API key."""
        del os.environ["OPENAI_API_KEY"]
        with self.assertRaises(ValueError) as context:
            AICodeGenerator()
        self.assertTrue("OPENAI_API_KEY required for code generation" in str(context.exception))

    @patch('ai_agent.openai.OpenAI')
    @patch('ai_agent.AICodeGenerator._parse_agent_response')
    @patch('ai_agent.openai.OpenAI.chat.completions.create', new_callable=AsyncMock)
    def test_generate_code_for_task_success(self, mock_create, mock_parse, MockOpenAI):
        """Test successful code generation."""
        mock_create.return_value.choices = [MagicMock(message=MagicMock(content="test content"))]
        mock_parse.return_value = [{"path": "test_file.py", "content": "print('hello')"}]

        generator = AICodeGenerator()
        result = asyncio.run(generator.generate_code_for_task("test task"))

        self.assertTrue(result['success'])
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['path'], "test_file.py")
        self.assertEqual(result['files'][0]['content'], "print('hello')")

    @patch('ai_agent.openai.OpenAI')
    @patch('ai_agent.openai.OpenAI.chat.completions.create', new_callable=AsyncMock)
    def test_generate_code_for_task_failure(self, mock_create, MockOpenAI):
        """Test code generation failure."""
        mock_create.side_effect = Exception("Test exception")

        generator = AICodeGenerator()
        result = asyncio.run(generator.generate_code_for_task("test task"))

        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Test exception")

    @patch('ai_agent.os.environ.get')
    def test_get_ai_code_generator(self, mock_get):
        """Test getting AI code generator instance."""
        mock_get.side_effect = lambda key: self.openai_key if key == "OPENAI_API_KEY" else "gpt-4o"
        
        generator = get_ai_code_generator()
        self.assertIsNotNone(generator)
        self.assertEqual(generator.model_name, "gpt-4o")

    @patch('ai_agent.os.environ.get')
    def test_get_ai_code_generator_missing_key(self, mock_get):
        """Test AI code generator instance when API key is missing."""
        mock_get.return_value = None
        
        generator = get_ai_code_generator()
        self.assertIsNone(generator)

    def tearDown(self):
        """Clean up test environment."""
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

if __name__ == '__main__':
    unittest.main()