import argparse
import asyncio
from wcps_game.main import main
from wcps_game import __version__


def run():
    parser = argparse.ArgumentParser(description="WCPS Game server")

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    parser.parse_args()

    # Run the asyncio main function
    asyncio.run(main())


if __name__ == "__main__":
    run()
