import unittest
from unittest.mock import patch, MagicMock
from github_helper import GitHubHelper

class TestGitHubHelper(unittest.TestCase):

    @patch('github_helper.GitHub')
    def setUp(self, MockGitHub):
        self.mock_github = MockGitHub.return_value
        self.helper = GitHubHelper("fake_token")

    def test_create_branch(self):
        repo_mock = MagicMock()
        repo_mock.create_git_ref.return_value = True
        self.mock_github.get_repo.return_value = repo_mock

        result = self.helper.create_branch("test-repo", "new-branch", "main")

        self.mock_github.get_repo.assert_called_once_with("test-repo")
        repo_mock.create_git_ref.assert_called_once_with(
            ref='refs/heads/new-branch', sha='main')
        self.assertTrue(result)

    def test_create_branch_fail(self):
        repo_mock = MagicMock()
        repo_mock.create_git_ref.side_effect = Exception("Create branch failed")
        self.mock_github.get_repo.return_value = repo_mock

        result = self.helper.create_branch("test-repo", "new-branch", "main")

        self.mock_github.get_repo.assert_called_once_with("test-repo")
        repo_mock.create_git_ref.assert_called_once_with(
            ref='refs/heads/new-branch', sha='main')
        self.assertFalse(result)

    def test_commit_files(self):
        repo_mock = MagicMock()
        repo_mock.create_git_commit.return_value = True
        self.mock_github.get_repo.return_value = repo_mock

        result = self.helper.commit_files(
            repo_name="test-repo",
            branch_name="main",
            commit_message="test commit",
            files={"path/to/file.txt": "file content"}
        )

        self.mock_github.get_repo.assert_called_once_with("test-repo")
        self.assertTrue(result)

    def test_commit_files_fail(self):
        repo_mock = MagicMock()
        repo_mock.create_git_commit.side_effect = Exception("Commit failed")
        self.mock_github.get_repo.return_value = repo_mock

        result = self.helper.commit_files(
            repo_name="test-repo",
            branch_name="main",
            commit_message="test commit",
            files={"path/to/file.txt": "file content"}
        )

        self.mock_github.get_repo.assert_called_once_with("test-repo")
        self.assertFalse(result)

    def test_create_pull_request(self):
        repo_mock = MagicMock()
        repo_mock.create_pull.return_value = True
        self.mock_github.get_repo.return_value = repo_mock

        result = self.helper.create_pull_request(
            repo_name="test-repo",
            title="Test PR",
            body="This is a test PR",
            head="feature-branch",
            base="main"
        )

        self.mock_github.get_repo.assert_called_once_with("test-repo")
        repo_mock.create_pull.assert_called_once_with(
            title="Test PR", body="This is a test PR", head="feature-branch", base="main")
        self.assertTrue(result)

    def test_create_pull_request_fail(self):
        repo_mock = MagicMock()
        repo_mock.create_pull.side_effect = Exception("Create PR failed")
        self.mock_github.get_repo.return_value = repo_mock

        result = self.helper.create_pull_request(
            repo_name="test-repo",
            title="Test PR",
            body="This is a test PR",
            head="feature-branch",
            base="main"
        )

        self.mock_github.get_repo.assert_called_once_with("test-repo")
        repo_mock.create_pull.assert_called_once_with(
            title="Test PR", body="This is a test PR", head="feature-branch", base="main")
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()