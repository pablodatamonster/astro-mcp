FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8080
CMD ["python", "-m", "astro_mcp.server"]
