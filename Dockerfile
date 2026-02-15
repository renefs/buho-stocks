FROM python:3.10-slim

WORKDIR /usr/src/

ENV PYTHONPATH "${PYTHONPATH}:/usr/src"
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV VIRTUAL_ENVIRONMENT_PATH /usr/src/.venv

LABEL org.opencontainers.image.authors='renefernandez@duck.com' \
      org.opencontainers.image.url='https://github.com/bocabitlabs/buho-stocks/pkgs/container/buho-stocks' \
      org.opencontainers.image.documentation='https://bocabitlabs.github.io/buho-stocks/' \
      org.opencontainers.image.source="https://github.com/bocabitlabs/buho-stocks" \
      org.opencontainers.image.vendor='Bocabitlabs (Rene Fernandez)' \
      org.opencontainers.image.licenses='GPL-3.0-or-later'

# Required to have netcat-openbsd
RUN apt-get update
RUN apt-get install default-libmysqlclient-dev netcat-openbsd gcc pkg-config -y

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY ./backend /usr/src/app
COPY ./etc /usr/src/etc

RUN chmod +x /usr/src/etc/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/src/etc/entrypoint.sh"]
