"""Asks the local model the questions in questions.json, with the offline library as its only tool.

Run inside the network-blocking sandbox (see run.sh): the model server (llama-server), this script
and openzim-mcp can reach only localhost. One JSON file per question lands in the output folder;
questions already answered are skipped, so a re-run continues where it stopped.
"""
import asyncio
import json
import os
import sys
import time
import urllib.request

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

API = "http://127.0.0.1:8090/v1/chat/completions"
ZIM_DIR = os.path.expanduser("~/zim-files")
MCP_BIN = os.path.expanduser("~/.local/bin/openzim-mcp")
MAX_STEPS = 8
TOOL_TEXT_LIMIT = 9000

SYSTEM = (
    "Ти помічник, який працює без інтернету. Твоє джерело фактів — офлайн-бібліотека через інструмент "
    "zim_query: Вікіпедія українською й англійською, медицина, ремонт (iFixit), виживання, вода, "
    "документація з програмування. Порядок роботи:\n"
    "1. Знайди: zim_query з query=\"search all files for <2-4 ключові слова англійською>\" "
    "(для українських тем — ще й українською).\n"
    "2. Прочитай: zim_query з query=\"get article <Path з результату>\" і zim_file_path=<файл із результату>. "
    "Відкрий 1-3 найкращі статті.\n"
    "3. Відповідай лише тим, що прочитав. Чого немає в статтях — не вигадуй, так і скажи.\n"
    "Рахунки, рівняння і код роби сам, без бібліотеки. Відповідь — українською, коротко, по кроках. "
    "Наприкінці: «Джерело: <стаття>, <файл>»."
)


def final_text(text):
    """The server keeps <think>…</think> in the text (reasoning-format none); the answer is what follows."""
    return text.split("</think>")[-1].replace("<think>", "").strip()


def chat(messages, tools):
    body = json.dumps({
        "model": "local", "messages": messages, **({"tools": tools} if tools else {}),
        "temperature": 0.6, "top_p": 0.95, "max_tokens": 6000,
    }).encode()
    req = urllib.request.Request(API, body, {"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=3600) as r:
        return json.load(r), time.time() - t


async def ask(session, tools, q):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q["text"]}]
    steps = []
    started = time.time()
    for step in range(MAX_STEPS):
        last = step == MAX_STEPS - 1
        if last:  # out of lookups: no tools this time, the model has to answer from what it read
            messages.append({"role": "user", "content": "Досить шукати. Дай відповідь з того, що вже прочитав."})
        r, dt = chat(messages, None if last else tools)
        m = r["choices"][0]["message"]
        steps.append({"type": "model", "seconds": round(dt, 1), "usage": r.get("usage"),
                      "timings": r.get("timings"), "reasoning": m.get("reasoning_content"),
                      "content": m.get("content"), "tool_calls": m.get("tool_calls")})
        messages.append({k: m[k] for k in ("role", "content", "tool_calls") if m.get(k) is not None})
        if not m.get("tool_calls"):
            break
        for tc in m["tool_calls"]:
            args = json.loads(tc["function"]["arguments"] or "{}")
            t = time.time()
            try:
                res = await session.call_tool(tc["function"]["name"], args)
                text = "\n".join(c.text for c in res.content if getattr(c, "text", None))
            except Exception as e:  # a failed search is part of the result, not a crash
                text = f"ERROR: {e}"
            steps.append({"type": "tool", "name": tc["function"]["name"], "args": args,
                          "seconds": round(time.time() - t, 1), "chars": len(text), "result": text[:4000]})
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": text[:TOOL_TEXT_LIMIT]})
    answer = final_text(next((s["content"] for s in reversed(steps) if s["type"] == "model" and s["content"]), ""))
    return {"id": q["id"], "question": q["text"], "answer": answer,
            "total_seconds": round(time.time() - started, 1), "steps": steps}


async def main(qfile, outdir):
    questions = json.load(open(qfile))
    params = StdioServerParameters(command=MCP_BIN, args=[ZIM_DIR],
                                   env={"OPENZIM_MCP_SEARCH__SEARCH_ALL_TOTAL_TIMEOUT_SECONDS": "120"})
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            listed = (await session.list_tools()).tools
            tools = [{"type": "function", "function": {"name": t.name, "description": t.description,
                                                       "parameters": t.input_schema}} for t in listed]
            for q in questions:
                out = os.path.join(outdir, q["id"] + ".json")
                if os.path.exists(out):
                    continue
                print(time.strftime("%H:%M:%S"), "asking", q["id"], flush=True)
                result = await ask(session, tools, q)
                json.dump(result, open(out, "w"), ensure_ascii=False, indent=1)
                print(time.strftime("%H:%M:%S"), "done", q["id"], result["total_seconds"], "s", flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
