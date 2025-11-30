#!/usr/bin/env python3
"""
Script to check current budget status for all users.
Displays user IDs, current message counts, and time until reset.
"""

import asyncio
import os

from dotenv import load_dotenv
from redis import asyncio as redis_asyncio

# Load environment variables from .env file
load_dotenv()


async def get_redis_client() -> redis_asyncio.Redis:
    """Create and return Redis client connection.

    Returns:
        redis_asyncio.Redis: Redis client configured from environment variables
    """
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    return redis_asyncio.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
    )


async def get_all_budget_data(
    redis_client: redis_asyncio.Redis,
) -> list[tuple[str, int, int]]:
    """Get all budget data from Redis.

    Args:
        redis_client: Redis client instance

    Returns:
        List of tuples containing (user_id, count, ttl)
    """
    budget_data = []

    try:
        # Use scan_iter to iterate through all budget keys
        async for key in redis_client.scan_iter("budget:*"):
            # Extract user_id from key format "budget:{user_id}"
            user_id = key.split(":", 1)[1]

            # Get the current count
            count = await redis_client.get(key)
            count = int(count) if count is not None else 0

            # Get TTL (time remaining in seconds)
            ttl = await redis_client.ttl(key)

            budget_data.append((user_id, count, ttl))

    except Exception as e:
        print(f"Error retrieving budget data: {e}")
        raise

    return budget_data


def format_ttl(ttl: int) -> str:
    """Format TTL for display.

    Args:
        ttl: Time to live in seconds

    Returns:
        Formatted TTL string
    """
    if ttl == -1:
        return "No expiry"
    elif ttl == -2:
        return "Key not found"
    elif ttl < 0:
        return "Invalid"
    elif ttl < 60:
        return f"{ttl}s"
    elif ttl < 3600:
        minutes = ttl // 60
        return f"{minutes}m"
    elif ttl < 86400:
        hours = ttl // 3600
        return f"{hours}h"
    else:
        days = ttl // 86400
        hours = (ttl % 86400) // 3600
        if hours > 0:
            return f"{days}d {hours}h"
        else:
            return f"{days}d"


def print_budget_table(budget_data: list[tuple[str, int, int]]) -> None:
    """Print budget information in a formatted table.

    Args:
        budget_data: List of tuples containing (user_id, count, ttl)
    """
    if not budget_data:
        print("No budget data found.")
        return

    # Table header
    print("=" * 60)
    print("USER BUDGET STATUS")
    print("=" * 60)
    print(f"{'USER ID':<15} | {'COUNT':<8} | {'TTL':<12}")
    print("-" * 60)

    # Sort by user ID for consistent output
    budget_data.sort(key=lambda x: x[0])

    # Print each row
    for user_id, count, ttl in budget_data:
        formatted_ttl = format_ttl(ttl)
        print(f"{user_id:<15} | {count:<8} | {formatted_ttl:<12}")

    print("-" * 60)
    print(f"Total users: {len(budget_data)}")
    print("=" * 60)


async def main() -> None:
    """Main function to check budget status."""
    try:
        print("Connecting to Redis...")
        redis_client = await get_redis_client()

        print("Retrieving budget data...")
        budget_data = await get_all_budget_data(redis_client)

        print_budget_table(budget_data)

        # Close the Redis connection using the recommended aclose() method
        await redis_client.aclose()

    except Exception as e:
        print(f"Error: {e}")
        print("Please check your Redis connection and environment variables.")
        print(f"REDIS_HOST: {os.getenv('REDIS_HOST', 'localhost')}")
        print(f"REDIS_PORT: {os.getenv('REDIS_PORT', '6379')}")


if __name__ == "__main__":
    asyncio.run(main())
