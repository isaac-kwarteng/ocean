# GitHub Cloud Integration for Port

This integration enables Port to sync resources from GitHub Cloud, including repositories, teams, issues, pull requests, and workflows.

## Features

- 🔄 Real-time synchronization of GitHub resources
- 📦 Repository management and metadata
- 👥 Team and member management
- 🐛 Issue tracking and management
- 🔄 Pull request tracking
- ⚡ GitHub Actions workflow management
- 🔐 Fine-grained access control
- 📊 Detailed resource metrics

## Prerequisites

- Python 3.11 or higher
- GitHub account with appropriate permissions
- Port account and API credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/ocean.git
cd ocean/integrations/github-cloud
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Unix/MacOS
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Update the `.env` file with your credentials:
```env
# Port credentials
PORT_CLIENT_ID=your_port_client_id
PORT_CLIENT_SECRET=your_port_client_secret

# GitHub credentials
OCEAN__INTEGRATION__CONFIG__GITHUB_TOKEN=your_github_token
OCEAN__INTEGRATION__CONFIG__GITHUB_ORG=your_github_org
```

### GitHub Token Requirements

The GitHub token needs the following permissions:
- `repo`: Full control of private repositories
- `workflow`: Access to GitHub Actions workflows
- `admin:org`: Full organization administration
- `admin:public_key`: Management of SSH keys

> **Note**: If you encounter a 403 error about token lifetime, consider using a fine-grained token instead of a classic token. Fine-grained tokens can bypass organization restrictions on token lifetime.

## Usage

1. Start the integration:
```bash
python main.py
```

2. The integration will automatically:
   - Sync repositories and their metadata
   - Sync teams and members
   - Sync issues and pull requests
   - Sync GitHub Actions workflows

## Resource Types

### Repositories
- Basic repository information
- Languages and topics
- Visibility and permissions
- Branch protection rules

### Teams
- Team membership
- Team permissions
- Team repositories

### Issues
- Issue status and labels
- Assignees and comments
- Milestones and projects

### Pull Requests
- PR status and reviews
- Merge status
- Review comments

### Workflows
- Workflow status
- Run history
- Job details

## Development

### Project Structure
```
github-cloud/
├── github/
│   ├── clients/           # GitHub API clients
│   │   ├── auth_client.py     # Authentication
│   │   ├── base_client.py     # Base client
│   │   ├── github_client.py   # Main client
│   │   └── rest_client.py     # REST API
│   ├── helpers/           # Helper functions
│   └── webhook/           # Webhook handlers
├── .port/                 # Port configuration
│   └── resources/         # Port resources
├── tests/                 # Test files
└── main.py               # Entry point
```

### Adding New Features

1. Create a new branch:
```bash
git checkout -b feature/your-feature
```

2. Implement your changes
3. Add tests
4. Submit a pull request

## Troubleshooting

### Common Issues

1. **403 Forbidden Error**
   - Check token permissions
   - Verify organization access
   - Consider using a fine-grained token

2. **Rate Limiting**
   - Check GitHub API rate limits
   - Implement rate limit handling
   - Use appropriate token scopes

3. **Missing Resources**
   - Verify token permissions
   - Check organization access
   - Validate resource paths

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
1. Check the [documentation](https://docs.getport.io)
2. Open an issue in this repository
3. Contact Port support at support@getport.io 
