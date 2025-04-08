# GitHub Cloud Integration for Port

This integration enables Port to interact with GitHub Cloud, allowing you to manage and track your GitHub resources within Port.

## Features

- Repository management
- Branch tracking
- Pull request monitoring
- Issue tracking
- Webhook support for real-time updates

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -e .
```

## Configuration

1. Create a GitHub Personal Access Token with the following scopes:
   - `repo` - Full control of private repositories
   - `workflow` - Update GitHub Action workflows
   - `admin:org` - Full organization administration
   - `admin:public_key` - Full management of public keys

2. Configure the integration in Port:
   - Add your GitHub Cloud credentials
   - Configure webhook endpoints
   - Set up resource mappings

## Usage

1. Start the integration:
```bash
python main.py
```

2. The integration will automatically:
   - Sync repositories
   - Track branches
   - Monitor pull requests
   - Process webhooks

## Development

### Project Structure

```
github-cloud/
├── src/
│   └── github_cloud/
│       ├── __init__.py
│       ├── integration.py
│       ├── client/
│       │   ├── __init__.py
│       │   └── github_client.py
│       └── webhook_processor/
│           ├── __init__.py
│           └── webhook_processor.py
├── tests/
│   └── ...
├── pyproject.toml
├── README.md
└── .gitignore
```

### Running Tests

```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 