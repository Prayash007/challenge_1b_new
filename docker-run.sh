#!/bin/bash
# Docker run scripts for Challenge 1B BERT Implementation
# Adobe Hackathon Challenge 1B

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="adobe-hackathon/challenge1b-bert"
CONTAINER_NAME="challenge1b-bert"

print_header() {
    echo -e "${BLUE}🤖 Adobe Hackathon Challenge 1B - BERT Docker${NC}"
    echo -e "${BLUE}🏆 Advanced BERT-based Document Ranking System${NC}"
    echo "================================================================"
}

build_image() {
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"
    docker build -t $IMAGE_NAME .
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
}

run_collection1() {
    echo -e "${YELLOW}🚀 Running BERT on Collection 1...${NC}"
    docker run --rm \
        -v "$(pwd)/Collection 1:/app/collections/Collection 1:ro" \
        -v "$(pwd)/output:/app/output:rw" \
        --name $CONTAINER_NAME \
        $IMAGE_NAME python run_collection.py --collection 1
}

run_all_collections() {
    echo -e "${YELLOW}🚀 Running BERT on all collections...${NC}"
    docker run --rm \
        -v "$(pwd):/app/collections:ro" \
        -v "$(pwd)/output:/app/output:rw" \
        --name $CONTAINER_NAME \
        $IMAGE_NAME python run_collection.py --all
}

run_interactive() {
    echo -e "${YELLOW}🖥️  Starting interactive BERT container...${NC}"
    docker run -it --rm \
        -v "$(pwd):/app/collections:ro" \
        -v "$(pwd)/output:/app/output:rw" \
        --name $CONTAINER_NAME \
        $IMAGE_NAME /bin/bash
}

start_with_compose() {
    echo -e "${YELLOW}🐳 Starting with Docker Compose...${NC}"
    docker-compose up --build
}

show_help() {
    echo -e "${GREEN}Usage: $0 [COMMAND]${NC}"
    echo ""
    echo "Commands:"
    echo "  build              Build the Docker image"
    echo "  run-collection1    Run BERT on Collection 1"
    echo "  run-all           Run BERT on all collections"
    echo "  interactive       Start interactive container"
    echo "  compose           Start with Docker Compose"
    echo "  help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build && $0 run-collection1"
    echo "  $0 compose"
    echo "  $0 interactive"
}

# Create output directory if it doesn't exist
mkdir -p output

# Main command handling
case "${1:-help}" in
    "build")
        print_header
        build_image
        ;;
    "run-collection1")
        print_header
        run_collection1
        ;;
    "run-all")
        print_header
        run_all_collections
        ;;
    "interactive")
        print_header
        run_interactive
        ;;
    "compose")
        print_header
        start_with_compose
        ;;
    "help"|*)
        print_header
        show_help
        ;;
esac

echo -e "${GREEN}🎉 BERT Docker operation complete!${NC}"
