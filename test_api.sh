#!/bin/bash
curl -X POST https://web3search-api.onrender.com/api/v1/deep-research \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh4eG5rYnh5amhob3JmZW9kaWppIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjYzODgwMiwiZXhwIjoyMDc4MjE0ODAyfQ.APx9XNJhCb2m4C7g5jPOqbG4WysG1uZe943afkofi7g" \
  -d '{"query": "What is Bitcoin?", "model_preset": "deepseek-chat"}'
