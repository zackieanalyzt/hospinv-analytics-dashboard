import sys
from loguru import logger
from runners.daily_pipeline import run_daily_pipeline
from runners.repair_runner import run_repair
from runners.backfill_runner import run_backfill

def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python main.py [daily|repair|backfill|job] [options]")
        sys.exit(1)

    command = sys.argv[1].lower()
    args = parse_args(sys.argv[2:]) if len(sys.argv) > 2 else {}

    if command == "daily":
        mode = args.get("mode", "incremental")
        run_daily_pipeline(mode=mode)

    elif command == "repair":
        run_repair(args)

    elif command == "backfill":
        run_backfill(args)

    elif command == "job":
        if len(sys.argv) < 3:
            logger.error("Usage: python main.py job ETL-001 [--mode incremental|full]")
            sys.exit(1)
        from runners.daily_pipeline import run_single_job
        mode = args.get("mode", "incremental")
        run_single_job(sys.argv[2], mode=mode)

    else:
        logger.error(f"Unknown command: {command}")
        sys.exit(1)

def parse_args(argv):
    args = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            key = argv[i][2:]
            value = argv[i + 1] if i + 1 < len(argv) else None
            args[key] = value
            i += 2
        else:
            i += 1
    return args

if __name__ == "__main__":
    main()
