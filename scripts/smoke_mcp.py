#!/usr/bin/env python3
"""Smoke-test an installed Nutrient PDF MCP server over stdio."""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from typing import Any

EXPECTED_TOOL_NAMES = ["get_pdf_object_tree", "resolve_indirect_object"]


class SmokeError(RuntimeError):
    """Raised when the installed MCP server does not satisfy the smoke contract."""


class ProcessOutput:
    """Drain a subprocess's output without risking a full-pipe deadlock."""

    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        if process.stdout is None or process.stderr is None:
            raise SmokeError("server process was started without output pipes")

        self.process = process
        self.stdout = process.stdout
        self.stderr = process.stderr
        self.stdout_lines: queue.Queue[bytes | None] = queue.Queue()
        self.stderr_chunks: list[bytes] = []
        self.stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self.stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self.stdout_thread.start()
        self.stderr_thread.start()

    def _read_stdout(self) -> None:
        try:
            for line in iter(self.stdout.readline, b""):
                self.stdout_lines.put(line)
        finally:
            self.stdout_lines.put(None)

    def _read_stderr(self) -> None:
        for chunk in iter(self.stderr.readline, b""):
            self.stderr_chunks.append(chunk)

    def next_stdout_line(self, deadline: float) -> bytes:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SmokeError("timed out waiting for a JSON-RPC response")

        try:
            line = self.stdout_lines.get(timeout=remaining)
        except queue.Empty as exc:
            raise SmokeError("timed out waiting for a JSON-RPC response") from exc

        if line is None:
            raise SmokeError(f"server closed stdout (exit code {self.process.poll()})")
        return line

    def finish(self) -> None:
        """Wait briefly for both output readers after the process exits."""
        self.stdout_thread.join(timeout=1)
        self.stderr_thread.join(timeout=1)

    def stderr_text(self) -> str:
        return b"".join(self.stderr_chunks).decode("utf-8", errors="replace").strip()


class MCPStdioClient:
    """Minimal newline-delimited JSON-RPC client for an MCP subprocess."""

    def __init__(self, process: subprocess.Popen[bytes], output: ProcessOutput) -> None:
        if process.stdin is None:
            raise SmokeError("server process was started without a stdin pipe")

        self.stdin = process.stdin
        self.output = output

    def send(self, message: dict[str, Any]) -> None:
        """Send one newline-delimited JSON-RPC message."""
        payload = json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\n"
        try:
            self.stdin.write(payload)
            self.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise SmokeError("server closed stdin before the smoke exchange completed") from exc

    def response(self, request_id: int, timeout: float) -> dict[str, Any]:
        """Read messages until the response matching request_id arrives."""
        deadline = time.monotonic() + timeout

        while True:
            line = self.output.next_stdout_line(deadline).strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise SmokeError(f"server emitted invalid JSON-RPC: {line!r}") from exc
            if not isinstance(message, dict):
                raise SmokeError(f"server emitted a non-object JSON-RPC message: {message!r}")
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise SmokeError(
                    f"request {request_id} returned JSON-RPC error: {message['error']!r}"
                )
            if "result" not in message:
                raise SmokeError(f"response {request_id} did not contain a result")
            return message


def stop_process(process: subprocess.Popen[bytes], require_clean_exit: bool) -> SmokeError | None:
    """Close stdin and stop the server, escalating only when necessary."""
    if process.stdin is not None and not process.stdin.closed:
        try:
            process.stdin.close()
        except OSError:
            pass

    try:
        exit_code = process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        if require_clean_exit:
            return SmokeError("server did not exit after stdin was closed")
        return None

    if require_clean_exit and exit_code != 0:
        return SmokeError(f"server exited with status {exit_code} after stdin was closed")
    return None


def assert_tools(response: dict[str, Any]) -> list[str]:
    """Assert that tools/list returns exactly the two public tools."""
    result = response.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("tools"), list):
        raise SmokeError(f"tools/list returned an invalid result: {result!r}")

    tools = result["tools"]
    names = [tool.get("name") if isinstance(tool, dict) else None for tool in tools]
    if not all(isinstance(name, str) for name in names) or sorted(names) != EXPECTED_TOOL_NAMES:
        raise SmokeError(
            "tools/list returned unexpected tool names: "
            f"expected {EXPECTED_TOOL_NAMES!r}, got {names!r}"
        )
    return sorted(names)


def run_smoke(entry_point: str, timeout: float) -> list[str]:
    """Run the MCP initialize handshake and verify the installed tool list."""
    child_env = os.environ.copy()
    child_env.pop("PYTHONPATH", None)

    try:
        process = subprocess.Popen(
            [entry_point],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=child_env,
        )
    except OSError as exc:
        raise SmokeError(f"could not launch installed entry point {entry_point!r}: {exc}") from exc

    output = ProcessOutput(process)
    client = MCPStdioClient(process, output)
    failure: SmokeError | None = None
    names: list[str] = []
    try:
        client.send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "wheel-smoke", "version": "1.0"},
                },
            }
        )
        client.response(1, timeout)
        client.send(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }
        )
        client.send(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }
        )
        names = assert_tools(client.response(2, timeout))
    except SmokeError as exc:
        failure = exc

    cleanup_failure = stop_process(process, require_clean_exit=failure is None)
    output.finish()
    if failure is None:
        failure = cleanup_failure

    if failure is not None:
        stderr = output.stderr_text()
        detail = f"\nserver stderr:\n{stderr}" if stderr else "\nserver stderr: <empty>"
        raise SmokeError(f"{failure}{detail}") from failure
    return names


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test an installed Nutrient PDF MCP entry point over stdio."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="maximum seconds to wait for each JSON-RPC response (default: 10)",
    )
    parser.add_argument("entry_point", help="path to the installed nutrient-pdf-mcp command")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        names = run_smoke(args.entry_point, args.timeout)
    except SmokeError as exc:
        print(f"MCP wheel smoke FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"MCP wheel smoke passed: tools={','.join(names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
