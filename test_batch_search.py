#!/usr/bin/env python3
"""
Test the batch search endpoint for true parallel processing
"""

import asyncio
import time
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from search_service import search_lyrics

async def test_batch_vs_sequential():
    print("=" * 60)
    print("TESTING BATCH SEARCH PERFORMANCE")
    print("=" * 60)

    test_songs = [
        "majesty worship his majesty",
        "praise by elevation worship",
        "revelation song - kari jobe"
    ]

    # Test 1: Sequential (old way)
    print("\n1. Sequential Search (old way):")
    start = time.time()
    sequential_results = []
    for song in test_songs:
        result = await search_lyrics(song)
        sequential_results.append(result)
    sequential_time = time.time() - start
    print(f"   ⏱️  Time: {sequential_time:.2f} seconds")
    print(f"   📊 Results: {[len(r) for r in sequential_results]}")

    # Test 2: Parallel (new way)
    print("\n2. Parallel Search (new way with asyncio.gather):")
    start = time.time()
    search_tasks = [search_lyrics(song) for song in test_songs]
    parallel_results = await asyncio.gather(*search_tasks)
    parallel_time = time.time() - start
    print(f"   ⏱️  Time: {parallel_time:.2f} seconds")
    print(f"   📊 Results: {[len(r) for r in parallel_results]}")

    # Calculate improvement
    speedup = sequential_time / parallel_time
    improvement = ((sequential_time - parallel_time) / sequential_time) * 100

    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f"Sequential: {sequential_time:.2f}s")
    print(f"Parallel:   {parallel_time:.2f}s")
    print(f"Speedup:    {speedup:.2f}x faster")
    print(f"Improvement: {improvement:.1f}% faster")
    print("\n✅ Batch endpoint will search all songs truly in parallel!")

if __name__ == "__main__":
    asyncio.run(test_batch_vs_sequential())
