from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("KITTYCREW_HOST", "127.0.0.1")
    port = int(os.getenv("KITTYCREW_PORT", "8731"))
    uvicorn.run("kittycrew.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()