"""CLI entrypoint for running the Fetch pipeline end-to-end.

Usage:
    python -m src.main --input "Sarah asked for the Q3 deck by Friday — get it done"
"""

from __future__ import annotations

import argparse
import asyncio

from dotenv import load_dotenv

from src.graph import build_graph
from src.state import AgentState


async def run(raw_input: str, source: str = "cli") -> AgentState:
    graph = build_graph()
    initial_state: AgentState = {
        "raw_input": raw_input,
        "source": source,
        "errors": [],
    }
    result = await graph.ainvoke(initial_state)
    return result


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the Fetch agent pipeline once.")
    parser.add_argument(
        "--input",
        required=True,
        help="The triggering ask, e.g. 'Sarah asked for the Q3 deck by Friday — get it done'",
    )
    parser.add_argument("--source", default="cli", choices=["cli", "slack", "gmail"])
    args = parser.parse_args()

    result = asyncio.run(run(args.input, source=args.source))
    print(result)


if __name__ == "__main__":
    main()
