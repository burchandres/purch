# Purch
Purch is a personal finance management app for every-day and long term finances.


## Setup
This application uses [uv](https://docs.astral.sh/uv/) as its python manager (both version and venvs). You can install it with the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or via homebrew:

```bash
brew install uv
```

The official installation is recommended.

To generate your `.env` file run

```bash
cp .env.template .env
```

To generate a secret key, in the python REPL, run

```python
import secrets; secrets.token_hex(16)
```

and that should output a secrets key that you must manuallly set as the `SECRET_KEY` in your .env, without quotes.

Now, run 

```bash
make setup
```

to install necessary packages for your virtual environment needed for development.

## Run

To run the application, there are two options: Docker or Locally (but with postgres still running in a docker container).

### Docker
```bash
make up
```

### Locally
```bash
make run-local
```
