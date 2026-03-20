# Multi-stage build for DocumentDB Functional Tests

# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 testrunner

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/testrunner/.local

# Copy application code
COPY documentdb_tests/ documentdb_tests/
COPY setup.py .

# Create directory for test results and set ownership
RUN mkdir -p .test-results && \
    chown -R testrunner:testrunner /app

# Switch to non-root user
USER testrunner

# Ensure scripts are in PATH
ENV PATH=/home/testrunner/.local/bin:$PATH

# Set Python to run unbuffered (so logs appear immediately)
ENV PYTHONUNBUFFERED=1

# Default command: run all tests
# Users can override with command line arguments
ENTRYPOINT ["pytest", "--rootdir", "documentdb_tests"]
CMD ["--help"]
