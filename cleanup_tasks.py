#!/usr/bin/env python3
"""Safe task queue cleanup utility."""

import logging

from modules.core.task_queue import TaskQueue


logging.basicConfig(level=logging.INFO)


def main() -> None:
    """Main cleanup function."""
    queue = TaskQueue("task_queue.json")

    print("📊 Current queue stats:")
    stats = queue.get_stats()
    for status, count in stats.items():
        print(f"  {status}: {count}")

    print("\n🔍 Cleanup preview (7 days):")
    preview = queue.preview_cleanup(max_age_days=7)
    print(f"  Total tasks: {preview['total_tasks']}")
    print(f"  To remove: {preview['tasks_to_remove']}")
    print(f"  To keep: {preview['tasks_to_keep']}")

    if preview["tasks_to_remove"] > 0:
        response = input("\n❓ Proceed with cleanup? (y/N): ")
        if response.lower() == "y":
            result = queue.safe_cleanup(max_age_days=7)
            print("\n✅ Cleanup completed:")
            print(f"  Removed: {result['removed_count']} tasks")
            print(f"  Remaining: {result['remaining_count']} tasks")
            print(f"  Backup created: {result['backup_created']}")
        else:
            print("❌ Cleanup cancelled")
    else:
        print("✨ No cleanup needed")


if __name__ == "__main__":
    main()
