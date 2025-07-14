#!/usr/bin/env python3
"""Continuous improvement loop for the agent."""

import logging
import signal
import time
from datetime import datetime

from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/continuous.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True


def signal_handler(signum, frame) -> None:
    """Handle shutdown signals gracefully."""
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False


def main() -> None:
    """Main continuous improvement loop."""
    global running

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("🚀 Starting continuous improvement loop...")

    cycle_count = 0

    try:
        while running:
            cycle_count += 1
            cycle_start = datetime.now()

            logger.info(f"🔄 Starting improvement cycle #{cycle_count}")

            try:
                # 1. Run unified fixer
                import subprocess

                result = subprocess.run(["python3", "unified_fixer.py"], capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    logger.info("✅ Code fixes applied")
                else:
                    logger.warning(f"⚠️ Fixer issues: {result.stderr}")

                # 2. Run main agent cycle
                result = subprocess.run(
                    ["python3", "run.py", "--mode", "auto"], capture_output=True, text=True, timeout=600
                )
                if result.returncode == 0:
                    logger.info("✅ Agent cycle completed")
                else:
                    logger.warning(f"⚠️ Agent issues: {result.stderr}")

                # 3. Clean old tasks periodically
                if cycle_count % 10 == 0:  # Every 10 cycles
                    from modules.core.task_queue import TaskQueue

                    queue = TaskQueue("task_queue.json")
                    cleaned = queue.safe_cleanup(max_age_days=3)
                    logger.info(f"🧹 Cleaned {cleaned['removed_count']} old tasks")

                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                logger.info(f"⏱️ Cycle #{cycle_count} completed in {cycle_duration:.1f}s")

                # Wait between cycles (adjustable)
                if running:
                    time.sleep(30)  # 30 seconds between cycles

            except subprocess.TimeoutExpired:
                logger.error("⏰ Cycle timeout - continuing to next cycle")
            except Exception as e:
                logger.error(f"❌ Cycle error: {e}")
                time.sleep(60)  # Wait longer on errors

    except KeyboardInterrupt:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007
        logger.info("🛑 Interrupted by user")
    finally:
        logger.info(f"🏁 Completed {cycle_count} improvement cycles")


if __name__ == "__main__":
    main()
