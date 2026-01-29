#!/bin/bash
# Demo script for LLM Configuration Management API
# This script demonstrates all the API endpoints

BASE_URL="http://localhost:8000/api/v1/llm"

echo "=========================================="
echo "LLM Configuration Management API Demo"
echo "=========================================="
echo ""

echo "1. List all LLM configurations"
echo "GET $BASE_URL/configs/"
curl -s "$BASE_URL/configs/" | python -m json.tool
echo ""
echo ""

echo "2. Get active providers"
echo "GET $BASE_URL/configs/active_providers/"
curl -s "$BASE_URL/configs/active_providers/" | python -m json.tool
echo ""
echo ""

echo "3. Get default provider"
echo "GET $BASE_URL/configs/default_provider/"
curl -s "$BASE_URL/configs/default_provider/" | python -m json.tool
echo ""
echo ""

echo "4. List analysis results"
echo "GET $BASE_URL/analysis-results/"
curl -s "$BASE_URL/analysis-results/" | python -m json.tool
echo ""
echo ""

echo "5. Get analysis statistics"
echo "GET $BASE_URL/analysis-results/stats/"
curl -s "$BASE_URL/analysis-results/stats/" | python -m json.tool
echo ""
echo ""

echo "=========================================="
echo "Demo completed!"
echo "=========================================="
echo ""
echo "Note: The following endpoints require authentication:"
echo "  - POST   $BASE_URL/configs/ (Create config - Admin only)"
echo "  - PUT    $BASE_URL/configs/{id}/ (Update config - Admin only)"
echo "  - DELETE $BASE_URL/configs/{id}/ (Delete config - Admin only)"
echo "  - POST   $BASE_URL/configs/{id}/test/ (Test connection)"
echo ""
echo "To test these endpoints, you need to:"
echo "  1. Create a user and get auth token"
echo "  2. Add 'Authorization: Token <your_token>' header"
