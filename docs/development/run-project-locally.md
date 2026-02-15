# 3. Install and run the project locally

1. [Backend](#backend)
2. [Client](#client)

## Backend

### Install Pyenv and Python version

I recommend using `pyenv` to install the Python version of your choice:

```bash
brew install pyenv
```

Install Python 3.11:

```bash
pyenv install 3.11
```

Activate Python 3.11 on the local folder:

```bash
pyenv local 3.11
```

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Dependencies

Install the Python dependencies:

```bash
uv sync --all-extras
```

Activate the virtual environment

```bash
source ./.venv/bin/activate
```

### Create a .env file

Create an `.env` on the root of the project by copying the content of `.env.sample` and populate its values to the desired ones.

### Running the initial migrations

```
cd backend
```

```bash
python manage.py migrate
```

### Running the application's backend

Backend:

```bash
python manage.py runserver
```

## Client

### Install the dependencies

```
cd client
```

```bash
npm install
```

### Running the application's frontend

```bash
npm start
```
