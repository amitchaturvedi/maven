# Building a Local Private MCP Client

This guide explains how to run a Multi‑Party Computation (MPC) client entirely on your local machine using the example scripts included in this repository.

## Prerequisites

- Python 3.8 or newer
- [virtualenv](https://virtualenv.pypa.io/en/latest/)
- Git

## Clone the Project

First, clone this repository or your fork of it:

```bash
git clone <URL-TO-YOUR-FORK>
```

Replace `<URL-TO-YOUR-FORK>` with the Git URL you want to use. Authenticate if the repository is private.

## Set Up a Virtual Environment

Create and activate a virtual environment to keep dependencies isolated:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

## Install Dependencies

If the project contains a `requirements.txt`, install the dependencies with:

```bash
pip install -r requirements.txt
```

If the project has other setup instructions, follow them as needed.

## Running the Client

Most MPC clients are started by executing a Python module or script. Consult the project files for the correct entry point. An example command might look like:

```bash
python app.py
```

This should start the client locally. Check the project documentation for any environment variables or configuration files that may be required.


## Example Client and Server

This repository includes simple example scripts in `docs/mcp-client` that show how to start an MCP server and interact with it using a local client.

1. Install the Python dependencies required by the examples:
   ```bash
   pip install llama-index mcp
   ```
2. Start the server:
   ```bash
   python docs/mcp-client/server.py --server_type sse
   ```
3. In a separate terminal, run the client:
   ```bash
   python docs/mcp-client/client.py
   ```
4. Enter messages to interact with the agent. Type `exit` to stop.

## Additional Resources

For more details about the MCP protocol and LlamaIndex integration, see the official project documentation.
