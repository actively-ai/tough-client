import asyncio
import itertools
import os
import re
import signal
import time
from datetime import datetime

import click
import httpx

# Default configuration
DEFAULT_SERVER_URL = "http://localhost:8000/completion"
DEFAULT_USER_ID = "default"
DEFAULT_DURATION = 60

MAX_LOGS = 10

# ANSI colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"


class Client:
    """
    A client that sends requests to a specified URL at a specified interval.
    Logs are maintained in an ordered dictionary (timestamp → message).
    """

    def __init__(
        self,
        client_id: int,
        n_chars: int,
        interval: float,
        user_id: str,
        url: str,
    ):
        self.client_name = f"CLIENT {client_id}"

        self.client_id = client_id
        self.n_chars = n_chars
        self.interval = interval
        self.user_id = user_id
        self.url = url

        # Statistics
        self.n_success = 0
        self.n_failure = 0

        # Logs: key is timestamp string, value is colorized message
        self.logs: dict[str, str] = {}
        self.max_logs = 10

    async def run(self, end_time: float) -> None:
        while time.time() < end_time:
            await self.run_once()
            await asyncio.sleep(self.interval)

    async def run_once(self) -> None:
        # Generate the prompt
        prompt = "A" * self.n_chars
        request_data = {"prompt": prompt, "user_id": self.user_id}

        # First log entry: "Sending ..."
        log_key = datetime.now().strftime("%H:%M:%S.%f")
        self.upsert_log(f"» Sending {self.n_chars}c...", BLUE, log_key)

        try:
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                response = await client.post(self.url, json=request_data, timeout=120.0)
                response_json = response.json()
                latency = time.time() - start_time

                if response.status_code == 200:
                    if response_json.get("n_chars") == self.n_chars:
                        self.n_success += 1
                        self.upsert_log(
                            f"✓ [200] Sent {self.n_chars}c ({latency:.2f}s)",
                            GREEN,
                            log_key,
                        )
                    else:
                        self.n_failure += 1
                        self.upsert_log("x [200] Incorrect response", RED, log_key)
                elif response.status_code == 429:
                    self.n_failure += 1
                    self.upsert_log("x [429] Rate limited", RED, log_key)
                else:
                    self.n_failure += 1
                    self.upsert_log(f"x [{response.status_code}] Error", RED, log_key)
        except Exception as e:
            self.n_failure += 1
            self.upsert_log(f"x Error: {e}", RED, log_key)

    def upsert_log(self, message: str, color: str, log_key: str) -> None:
        colored_message = f"{color}{message}{RESET}"
        self.logs[log_key] = colored_message

    def get_success_rate(self) -> float:
        total = self.n_success + self.n_failure
        return (self.n_success / total * 100) if total > 0 else 0

    def get_stats_output(self) -> list[str]:
        """
        Returns formatted statistics lines for display.
        """
        lines = []
        total_requests = self.n_success + self.n_failure

        # Header
        display_name = f"{self.client_name} ({self.n_chars}c/{self.interval}s)"
        lines.append(f"{BOLD}{display_name}{RESET}")

        # Stats
        lines.append(f"{GREEN}✓ Successful requests: {self.n_success}{RESET}")
        lines.append(f"{RED}✗ Failed requests: {self.n_failure}{RESET}")

        if total_requests > 0:
            success_rate = self.get_success_rate()
            if success_rate > 80:
                color = GREEN
            elif success_rate > 50:
                color = YELLOW
            else:
                color = RED
            lines.append(f"{color}Success rate: {success_rate:.1f}%{RESET}")

        return lines


class Display:
    """
    Responsible for printing the logs of one or more clients side by side.
    """

    @staticmethod
    def _clear() -> None:
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def _get_term_width() -> int:
        try:
            return os.get_terminal_size().columns
        except Exception:
            return 80

    @staticmethod
    def _get_header(client: Client) -> str:
        return (
            f"{BOLD}{client.client_name} ({client.n_chars}c/{client.interval}s){RESET}"
        )

    @staticmethod
    def ansi_ljust(text: str, width: int) -> str:
        """
        Left-justify text with ANSI color codes, accounting for the invisible ANSI characters.
        """
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

        # Remove ANSI sequences to get the visible length
        visible_text = ansi_escape.sub("", text)
        visible_length = len(visible_text)

        # Calculate padding needed
        padding = max(0, width - visible_length)

        # Add padding to the end of the original text (with ANSI codes)
        return text + " " * padding

    @staticmethod
    def display_logs(client1: Client, client2: Client) -> None:
        Display._clear()

        term_width = Display._get_term_width()
        pane_width = max(20, (term_width - 3) // 2)
        separator = "|"

        header1 = Display._get_header(client1)
        header2 = Display._get_header(client2)

        header1_wrapped = Display.ansi_ljust(header1, width=pane_width)
        header2_wrapped = Display.ansi_ljust(header2, width=pane_width)

        print(f"{header1_wrapped} {separator} {header2_wrapped}")
        print("-" * term_width)

        # Take only the most recent MAX_LOGS logs
        client1_logs = list(client1.logs.items())[-MAX_LOGS:]
        client2_logs = list(client2.logs.items())[-MAX_LOGS:]

        # Pair them up so we can display in two columns
        logs = itertools.zip_longest(client1_logs, client2_logs, fillvalue=None)

        for log1, log2 in logs:
            text1 = ""
            if log1:
                timestamp, message = log1
                text1 = f"{timestamp} | {message}"

            text2 = ""
            if log2:
                timestamp, message = log2
                text2 = f"{timestamp} | {message}"

            # Wrap or truncate each side to one line within pane_width
            text1_wrapped = Display.ansi_ljust(text1, width=pane_width)
            text2_wrapped = Display.ansi_ljust(text2, width=pane_width)

            # Print them side by side
            print(f"{text1_wrapped} {separator} {text2_wrapped}")

    @staticmethod
    def display_results(
        clients: list[Client], duration: int, user_id: str, server_url: str
    ):
        """
        Print final results after the simulation completes.
        """
        print("\n\n")
        print(f"{MAGENTA}{'=' * 80}{RESET}")
        print(f"{BOLD}{MAGENTA}SIMULATION RESULTS{RESET}")
        print(f"{MAGENTA}{'=' * 80}{RESET}")

        print(f"\n{CYAN}User ID: {user_id}{RESET}")
        print(f"{CYAN}Server URL: {server_url}{RESET}")
        print(f"{CYAN}Duration: {duration} seconds{RESET}\n")

        for client in clients:
            stats = client.get_stats_output()
            print("\n".join(stats))
            print()

        print(f"{MAGENTA}{'=' * 80}{RESET}")

    @staticmethod
    async def run(client1: Client, client2: Client, end_time: float) -> None:
        while time.time() < end_time:
            Display.display_logs(client1, client2)
            await asyncio.sleep(0.5)


class Simulator:
    def __init__(self, user_id: str, url: str, duration: int):
        self.user_id = user_id
        self.url = url
        self.duration = duration

        self.client1 = Client(
            client_id=1, n_chars=16, interval=1.0, user_id=self.user_id, url=self.url
        )
        self.client2 = Client(
            client_id=2, n_chars=32, interval=8.0, user_id=self.user_id, url=self.url
        )

    async def start(self) -> None:
        loop = asyncio.get_event_loop()

        # Graceful shutdown on SIGINT / SIGTERM
        # Handle signals differently on Windows vs Unix systems
        if os.name == 'nt':  # Windows
            # Windows doesn't support SIGTERM the same way
            # and add_signal_handler doesn't work properly
            pass
        else:  # Unix/Linux/Mac
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig, lambda: print("\nSimulation interrupted.") or loop.stop()
                )

        end_time = time.time() + self.duration

        coros = [
            self.client1.run(end_time),
            self.client2.run(end_time),
            Display.run(self.client1, self.client2, end_time),
        ]
        await asyncio.gather(*coros)

        Display.display_results(
            clients=[self.client1, self.client2],
            duration=self.duration,
            user_id=self.user_id,
            server_url=self.url,
        )


@click.command()
@click.argument("user_id", type=str, required=True)
@click.argument("url", type=str, default=DEFAULT_SERVER_URL)
@click.argument("duration", type=int, default=DEFAULT_DURATION)
def main(user_id: str, url: str, duration: int):
    simulator = Simulator(user_id=user_id, url=url, duration=duration)

    print(f"Starting simulation for {duration} seconds...")
    print(f"User ID: {user_id}")
    print(f"Server URL: {url}")

    time.sleep(1)

    try:
        asyncio.run(simulator.start())
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")


if __name__ == "__main__":
    main()
