from typing import Iterable
import httpx
import sys
from prompt_toolkit.completion import CompleteEvent, Completion, Completer
from prompt_toolkit.completion.base import CompleteEvent, Completion
from prompt_toolkit.document import Document
from rich.console import Console
from prompt_toolkit import prompt
import json

c = Console()


class WordCompleter(Completer):
    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        if len(document.text) <= 1:
            return []
        url = (
            "http://dict.iciba.com/dictionary/word/suggestion?word=%s&nums=5"
            % document.text
        )
        try:
            for w in httpx.get(url).json()["message"]:
                yield Completion(w["key"], start_position=-len(document.text))
        except:
            return []


def main():
    if len(sys.argv) < 2:
        word = prompt(
            "Word: ",
            completer=WordCompleter(),
            complete_in_thread=True,
            complete_while_typing=True,
        )
    elif len(sys.argv) > 2:
        c.print("[cyan]Usage: [/cyan] main.py <word>")
        return
    else:
        word = sys.argv[1]

    url = "https://www.iciba.com/word?w=" + word

    with c.status("Querying for '%s'..." % word):
        resp = httpx.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0"
            },
        )
        data = resp.text.split("</script></body></html>")[0]
        data = data.split('<script id="__NEXT_DATA__" type="application/json">')[1]
        data = json.loads(data)["props"]["pageProps"]["initialReduxState"]["word"][
            "wordInfo"
        ]
        # c.print(data)

    try:
        s = data["baesInfo"]["symbols"][0]
    except KeyError:
        c.print("[red]Word not found[/red]")
        exit(1)

    ph = s["ph_en"]
    if len(s["ph_am"]) > 0:
        ph = s["ph_am"]
    if len(s["ph_other"]) > 0:
        ph = s["ph_other"]
    c.print(data["baesInfo"]["word_name"], "[i]" + ph + "[/i]")

    meanings = "\n[bold]= Meanings: [/bold] \n"

    for part in data["baesInfo"]["symbols"][0]["parts"]:
        meanings += "[cyan][bold]" + part["part"] + "[/cyan][/bold] "
        meanings += "; ".join(part["means"])
        meanings += "\n"

    c.print(meanings)

    synonyms = "[bold]= Synonyms: [/bold] \n"

    if "synonym" in data:
        for synonym in data["synonym"]:
            for m in synonym["means"]:
                if len(synonym["part_name"]) > 0:
                    synonyms += (
                        "[cyan][bold]" + synonym["part_name"] + "[/cyan][/bold] "
                    )
                synonyms += m["word_mean"] + "\n"
                synonyms += ", ".join(m["cis"])
                synonyms += "\n"

        c.print(synonyms)

    c.print("[bold]= Other forms: [/bold][i]" + ", ".join(data["exchanges"]) + "[/i]")


def start():
    try:
        main()
    except KeyboardInterrupt:
        c.print("[yellow]User Interrupt[/yellow]")
    except EOFError:
        pass
    except Exception:
        c.print_exception()


if __name__ == "__main__":
    start()
