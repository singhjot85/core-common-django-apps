ARG PYTHON_VERSION=3.12

# ==================================================
# Stage 0: Fetch the official python docker image
# ==================================================
FROM python:${PYTHON_VERSION}-slim AS python-image


# =====================================================
# Step 1 (Build Stage): Dependencies installation layer
# =====================================================
FROM python-image AS python-build-stage

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    pipx \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install poetry==2.4.1 && \
    pipx inject poetry poetry-plugin-export

# Use pipx environment to get the actual path
# ENV PATH="$(pipx environment --value PIPX_BIN_DIR):${PATH}"
ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml poetry.lock /

RUN poetry export \
    -f requirements.txt \
    --output requirements.txt \
    --without-hashes

RUN pip wheel \
    --wheel-dir /usr/src/app/wheels \
    -r requirements.txt

# ===============================================================================
# Step 2 (Run Stage): Whatever is installed, ship in final image along with code
# ================================================================================
FROM python-image AS python-run-stage

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed wheels
COPY --from=python-build-stage /usr/src/app/wheels /wheels

# Install dependencies from wheels
RUN pip install --no-cache-dir \
    --no-index \
    --find-links=/wheels \
    /wheels/* \
    && rm -rf /wheels

# Set a work-directory and copy backend code
WORKDIR /backend
COPY . /backend
COPY ./sample_project/compose/local/backend/scripts /scripts
RUN chmod +x /scripts/*.sh

CMD ["/scripts/django-start.sh"]
