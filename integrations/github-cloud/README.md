# Port Ocean GitHub Integration

This integration allows you to sync your GitHub resources with Port. It supports repositories, teams, issues, pull requests, and workflows.

## Features

- Real-time synchronization of GitHub resources
- Support for multiple resource types:
  - Repositories
  - Teams
  - Issues
  - Pull Requests
  - Workflows
- Webhook support for real-time updates
- Configurable polling intervals
- Comprehensive error handling and logging

## Prerequisites

- Python 3.9 or higher
- Poetry for dependency management
- A GitHub account with appropriate permissions
- A Port account with API credentials

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/port-labs/ocean.git
   cd ocean/integrations/github
   ```

2. Install dependencies:
   ```bash
   make install
   ```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the environment variables in `.env`:
   ```
   OCEAN__PORT__CLIENT_ID="your-port-client-id"
   OCEAN__PORT__CLIENT_SECRET="your-port-client-secret"
   OCEAN__INTEGRATION__IDENTIFIER=github
   OCEAN__PORT__BASE_URL=https://api.getport.io
   OCEAN__EVENT_LISTENER__TYPE=POLLING
   OCEAN__INITIALIZE_PORT_RESOURCES=true

   OCEAN__INTEGRATION__CONFIG__TOKEN="your-github-token"
   OCEAN__INTEGRATION__CONFIG__ORGANIZATION="your-github-org"
   OCEAN__BASE_URL=https://api.github.com
   ```

## Usage

1. Start the integration:
   ```bash
   poetry run python -m github
   ```

2. The integration will automatically:
   - Initialize Port resources based on your GitHub data
   - Set up webhook listeners or polling as configured
   - Start syncing data between GitHub and Port

## Development

- Format code:
  ```bash
  make format
  ```

- Run linters:
  ```bash
  make lint
  ```

- Run tests:
  ```bash
  make test
  ```

- Generate coverage report:
  ```bash
  make coverage
  ```

## Contributing

Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you need help or have any questions, please:

1. Check the [documentation](https://docs.getport.io)
2. Join our [Discord community](https://discord.gg/port-labs)
3. Open an issue on GitHub
4. Contact support@getport.io 