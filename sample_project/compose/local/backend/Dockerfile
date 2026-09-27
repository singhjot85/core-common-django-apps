ARG PYTHON_VERSION=3.12

# ==================================================
# Stage 0: Fetch the official python docker image
# ==================================================
FROM python:${PYTHON_VERSION} AS python-image


# =====================================================
# Step 1 (Build Stage): Dependencies installation layer
# =====================================================
FROM python-image AS python-build-stage

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    pipx \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install poetry==2.4.1 && \
    pipx inject poetry poetry-plugin-export

# Use pipx environment to get the actual path
# ENV PATH="$(pipx environment --value PIPX_BIN_DIR):${PATH}"
ENV PATH="/root/.local/bin:${PATH}"

COPY ./backend/pyproject.toml ./backend/poetry.lock /

RUN poetry export \
    -f requirements.txt \
    --output requirements.txt \
    --without-hashes

RUN pip wheel \
    --wheel-dir /usr/src/app/wheels \
    -r requirements.txt

# ===============================================================================
# Step 3 (Run Stage): Whatever is installed, ship in final image along with code
# ================================================================================
FROM python-image AS python-run-stage

# Copy installed wheels
COPY --from=python-build-stage /usr/src/app/wheels /wheels

# Install dependencies from wheels
RUN pip install --no-cache-dir \
    --no-index \
    --find-links=/wheels \
    /wheels/*

# Set a work-directory and copy backend code
WORKDIR /backend
COPY ./backend /backend

CMD ["/scripts/django-start.sh"]
