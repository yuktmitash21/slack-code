# Additional Documentation for Slack Bot with GitHub Integration and AI Code Generation

This document provides further insights and advanced configuration options for the Slack bot designed to integrate with GitHub and leverage AI for code generation.

## Advanced Configuration

### Environment Variables

Beyond the typical setup, additional environment variables can be configured for enhanced functionality:

- **LOG_LEVEL**: Set the logging level to control the verbosity of the bot's output. Options include `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- **MAX_RETRIES**: Define the maximum number of retries for API calls to Slack and GitHub in case of transient errors.
- **CACHE_EXPIRATION**: Set the duration (in seconds) for how long cached AI responses should be stored.

Example `.env` additions: