# AI Gym Bro - Telegram Bot with OpenAI Integration

A Telegram bot that integrates with OpenAI's API to provide AI-powered assistance.

## Development Setup

### Prerequisites

- Docker
- Docker Compose
- VS Code with Remote - Containers extension

### Getting Started

1. Clone the repository
2. Create a `.env` file in the root directory with the following variables:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   ```
3. Open the project in VS Code
4. When prompted, click "Reopen in Container" or use the command palette (Ctrl+Shift+P) and select "Remote-Containers: Reopen in Container"

### Development

The project uses Poetry for dependency management. The development environment is set up in a Docker container with all necessary tools and configurations.

#### Available Commands

- `poetry run python -m bot` - Run the bot
- `poetry run pytest` - Run tests
- `poetry run black .` - Format code
- `poetry run ruff check .` - Lint code
- `poetry run mypy .` - Type checking

### Project Structure

```
.
├── .devcontainer/        # VS Code devcontainer configuration
├── bot/                  # Bot source code
├── tests/               # Test files
├── .env                 # Environment variables
├── Dockerfile          # Docker configuration
├── pyproject.toml      # Poetry configuration
└── README.md           # This file
```

## License

This project is licensed under the terms of the LICENSE file. 