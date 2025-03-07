# mcpPaylocity MCP Server
[![smithery badge](https://smithery.ai/badge/@mz462/mcp-paylocity)](https://smithery.ai/server/@mz462/mcp-paylocity)

A Model Context Protocol (MCP) server to fetch data from Paylocity API endpoints.

## Components

### Resources

The server implements Paylocity API resources with:
- Custom `paylocity://` URI scheme for accessing Paylocity data
- The following resources are available:
  - `paylocity://employees/{company_id}` - List all employees for a company
  - `paylocity://employees/{company_id}/{employee_id}` - Get details for a specific employee
  - `paylocity://earnings/{company_id}/{employee_id}` - Get earnings data for a specific employee
  - `paylocity://codes/{company_id}/{code_resource}` - Get company codes for a specific resource
  - `paylocity://localtaxes/{company_id}/{employee_id}` - Get local taxes for a specific employee
  - `paylocity://paystatement/{company_id}/{employee_id}/{year}/{check_date}` - Get pay statement details for a specific date

### Tools

The server implements the following tools:
- `fetch_employees` - Fetches all employees for a company
  - Takes optional `company_id` parameter
- `fetch_employee_details` - Fetches details for a specific employee
  - Takes required `employee_id` and optional `company_id` parameters
- `fetch_employee_earnings` - Fetches earnings data for a specific employee
  - Takes required `employee_id` and optional `company_id` parameters
- `fetch_company_codes` - Fetches company codes for a specific resource
  - Takes required `code_resource` and optional `company_id` parameters
- `fetch_employee_local_taxes` - Fetches local taxes for a specific employee
  - Takes required `employee_id` and optional `company_id` parameters
- `fetch_employee_paystatement_details` - Fetches pay statement details for a specific date
  - Takes required `employee_id`, `year`, `check_date` and optional `company_id` parameters

## Future Implementations

The following endpoints will be implemented in future updates:

- [ ] Additional employee endpoints (emergency contacts, primary pay rates, etc.)
- [ ] Deductions endpoints
- [ ] Benefits enrollment endpoints
- [ ] Direct deposit endpoints
- [ ] Additional company setup endpoints

## Configuration

The server requires the following environment variables to be set:
- `PAYLOCITY_CLIENT_ID` - Your Paylocity API client ID
- `PAYLOCITY_CLIENT_SECRET` - Your Paylocity API client secret
- `PAYLOCITY_COMPANY_IDS` - Comma-separated list of company IDs to use
- `PAYLOCITY_ENVIRONMENT` - API environment to use (`production` or `testing`)

These can be set in a `.env` file in the project root directory.

## Security

⚠️ **IMPORTANT**: This application caches authentication tokens in the `src/mcppaylocity/access_token/` directory. These files contain sensitive credentials and should **never** be committed to version control.

The repository includes these paths in `.gitignore`, but please verify that token files are not accidentally committed when pushing changes.

If you've accidentally committed token files, follow these steps:
1. Remove the files from the repository: `git rm --cached src/mcppaylocity/access_token/token.json src/mcppaylocity/access_token/token_info.txt`
2. Commit the removal: `git commit -m "Remove accidentally committed token files"`
3. Consider rotating your Paylocity API credentials as they may have been compromised

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  
  ```json
  "mcpServers": {
    "mcpPaylocity": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcpPaylocity",
        "run",
        "mcppaylocity"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  
  ```json
  "mcpServers": {
    "mcpPaylocity": {
      "command": "uvx",
      "args": [
        "mcppaylocity"
      ]
    }
  }
  ```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcpPaylocity run mcppaylocity
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

## Architecture

The server is built with the following components:

1. **PaylocityClient** - Handles communication with the Paylocity API
2. **TokenManager** - Manages authentication tokens, including caching and renewal
3. **FastMCP Server** - Exposes Paylocity data through MCP resources and tools

## License

MIT License

Copyright (c) 2024 MJ Zou ([@mjzou](https://www.linkedin.com/in/mjzou/))

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
