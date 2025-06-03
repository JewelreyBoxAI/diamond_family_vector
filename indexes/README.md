# FAISS Indexes Directory

This directory contains FAISS vector indexes for semantic search functionality.

## Structure

- `default/` - Default semantic index for general queries
- `faqs/` - FAQ-specific semantic index  
- `products/` - Product-related semantic index
- `services/` - Service-related semantic index
- `design/` - Design consultation semantic index

## Usage

The memory_manager automatically routes queries to appropriate indexes based on intent classification. If indexes are not available, the system gracefully falls back to basic intent matching using the `intents.json` file.

## Building Indexes

To build semantic indexes, use the `build_faiss_index()` function in memory_manager.py with appropriate document collections.

**Note**: Semantic search is optional. The system works perfectly with basic intent matching if FAISS libraries are not available. 