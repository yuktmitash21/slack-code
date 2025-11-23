import unittest
from unittest.mock import patch, MagicMock
from slack_bolt import App
from slack_bot import slack_event_handler  # Assuming this is the event handler function in slack_bot.py

class TestSlackBot(unittest.TestCase):

    @patch('slack_bolt.App')
    def setUp(self, MockApp):
        self.mock_app = MockApp.return_value
        self.mock_app.client = MagicMock()
        self.mock_app.client.chat_postMessage = MagicMock()
        self.mock_event_data = {
            "event": {
                "type": "app_mention",
                "text": "<@U12345> test message",
                "channel": "C12345",
                "user": "U67890"
            }
        }

    def test_app_mention_response(self):
        slack_event_handler(self.mock_app, self.mock_event_data)
        self.mock_app.client.chat_postMessage.assert_called_once_with(
            channel="C12345",
            text="Hello <@U67890>, how can I assist you today?"
        )

    @patch('slack_bolt.App')
    def test_event_no_mention(self, MockApp):
        mock_app = MockApp.return_value
        mock_event_data = {
            "event": {
                "type": "message",
                "text": "Just a regular message",
                "channel": "C12345",
                "user": "U67890"
            }
        }
        slack_event_handler(mock_app, mock_event_data)
        mock_app.client.chat_postMessage.assert_not_called()

    @patch('slack_bot.github_helper.create_pull_request')
    def test_create_pull_request(self, mock_create_pr):
        mock_create_pr.return_value = "PR created successfully"
        response = slack_event_handler(self.mock_app, {
            "event": {
                "type": "app_mention",
                "text": "<@U12345> make PR",
                "channel": "C12345",
                "user": "U67890"
            }
        })
        self.assertEqual(response, "PR created successfully")
        mock_create_pr.assert_called_once()

    def test_handle_invalid_event_type(self):
        invalid_event_data = {
            "event": {
                "type": "invalid_event",
                "text": "<@U12345> something",
                "channel": "C12345",
                "user": "U67890"
            }
        }
        response = slack_event_handler(self.mock_app, invalid_event_data)
        self.assertIsNone(response)

if __name__ == '__main__':
    unittest.main()