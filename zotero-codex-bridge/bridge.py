#!/usr/bin/env python3
"""
Zotero <-> Codex 本地桥接服务

把本机已用 ChatGPT 账号登录的 Codex CLI（`codex exec`）包装成一个
OpenAI 兼容的 /v1/chat/completions 接口，供 Zotero 的 AI 插件调用。
不需要 OpenAI API Key，消耗的是 ChatGPT 套餐里的 Codex 额度。

只依赖 Python 3.8+ 标准库。默认只监听 127.0.0.1。

用法：
    python3 bridge.py                     # 默认端口 8765
    python3 bridge.py --port 8765 --token 任意字符串 --workdir ~/ScienceMentor

在 Zotero 插件中填写：
    API Base URL : http://127.0.0.1:8765/v1
    API Key      : 与 --token 相同（未设置 --token 时随便填）
    Model        : codex-translate / codex-explain / codex-mentor / codex
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SKILL_NAME = "scientific-taste-mentor"

# 每个“模型”对应一种用途：附加指令、沙箱权限、推理强度
MODES = {
    "codex-translate": {
        "instruction": (
            "你是学术翻译。把用户提供的文本翻译成准确、通顺的简体中文学术语言；"
            "若原文是中文则译成英文。保留公式、变量名、引用编号和专有名词（首次出现时可括注原文）。"
            "只输出译文，不要解释，不要运行任何命令，不要读写文件。"
        ),
        "sandbox": "read-only",
        "effort": "low",
    },
    "codex-explain": {
        "instruction": (
            "你是耐心的科研助教。用户在读论文时遇到了不懂的内容。请用简体中文："
            "1) 先用一两句话说清它是什么；2) 解释它在这段/这篇论文里起什么作用；"
            "3) 必要时给一个直观例子或公式含义。区分论文原文明确说的内容和你的推断。"
            "不要运行任何命令，不要读写文件。"
        ),
        "sandbox": "read-only",
        "effort": "medium",
    },
    "codex-mentor": {
        "instruction": (
            f"请使用 ${SKILL_NAME} 技能（科学审美导师），严格遵守其规则："
            "一次只问一个判断题、用户作答前不公布答案、评价锚定论文原文并标注"
            "【作者事实】【AI推断】【待验证假设】。"
            "用户已指定并确认训练记录路径为：{log_path} ，直接读取/追加该文件，无需再询问路径。"
            "每次只回复一轮（出完一题就结束本轮）。"
            "以下是 Zotero 中的完整对话历史（含论文内容），请接着最后一条用户消息继续。"
        ),
        "sandbox": "workspace-write",  # 允许在 workdir 中写训练记录
        "effort": "high",
    },
    "codex": {
        "instruction": "以下是来自 Zotero 的对话，请回复最后一条用户消息。不要运行任何命令，不要读写文件。",
        "sandbox": "read-only",
        "effort": None,  # 使用 Codex 配置默认值
    },
}


def log(*args):
    print(time.strftime("[%H:%M:%S]"), *args, file=sys.stderr, flush=True)


def content_to_text(content, image_dir, images):
    """OpenAI 消息 content 可能是字符串或分段数组；提取文本，保存图片。"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for part in content:
        if not isinstance(part, dict):
            continue
        ptype = part.get("type")
        if ptype in ("text", "input_text"):
            parts.append(part.get("text", ""))
        elif ptype in ("image_url", "input_image"):
            url = part.get("image_url")
            if isinstance(url, dict):
                url = url.get("url")
            if isinstance(url, str) and url.startswith("data:") and ";base64," in url:
                header, data = url.split(";base64,", 1)
                ext = header.split("/")[-1] or "png"
                path = os.path.join(image_dir, f"img{len(images)}.{ext}")
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                images.append(path)
                parts.append(f"[图片 {len(images)} 已附上]")
    return "\n".join(parts)


def build_prompt(mode, messages, image_dir, images, log_path=""):
    role_names = {"system": "系统/插件指令", "user": "用户", "assistant": "助手", "tool": "工具结果"}
    lines = [MODES[mode]["instruction"].replace("{log_path}", log_path), ""]
    for m in messages:
        text = content_to_text(m.get("content"), image_dir, images).strip()
        if not text:
            continue
        lines.append(f"===== {role_names.get(m.get('role'), m.get('role'))} =====")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


class Bridge:
    def __init__(self, args):
        self.args = args
        self.codex = args.codex or shutil.which("codex")
        if not self.codex:
            sys.exit("找不到 codex 命令。请先安装 Codex CLI 并运行 `codex login`（选择 ChatGPT 登录）。")
        self.sem = threading.Semaphore(args.max_concurrency)
        os.makedirs(args.workdir, exist_ok=True)
        self.log_path = os.path.join(os.path.abspath(args.workdir), "research-training", "judgment-log.md")

    def run(self, mode, messages, model_override=None):
        cfg = MODES[mode]
        with tempfile.TemporaryDirectory(prefix="zcb-") as tmp:
            images = []
            prompt = build_prompt(mode, messages, tmp, images, self.log_path)
            out_file = os.path.join(tmp, "last.txt")
            cmd = [
                self.codex, "exec",
                "--skip-git-repo-check",
                "--ephemeral",
                "--color", "never",
                "-s", cfg["sandbox"],
                "-C", self.args.workdir,
                "-o", out_file,
            ]
            if cfg["effort"]:
                cmd += ["-c", f'model_reasoning_effort="{cfg["effort"]}"']
            if model_override or self.args.model:
                cmd += ["-m", model_override or self.args.model]
            for img in images:
                cmd += ["-i", img]
            cmd.append("-")  # 从 stdin 读取 prompt（避免命令行长度限制）

            with self.sem:
                t0 = time.time()
                proc = subprocess.run(
                    cmd, input=prompt, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=self.args.timeout,
                )
                log(f"{mode}: codex 退出码 {proc.returncode}，用时 {time.time() - t0:.1f}s，prompt {len(prompt)} 字符")

            answer = ""
            if os.path.exists(out_file):
                with open(out_file, encoding="utf-8", errors="replace") as f:
                    answer = f.read().strip()
            if proc.returncode != 0 or not answer:
                err = (proc.stderr or proc.stdout or "").strip()[-2000:]
                raise RuntimeError(f"codex exec 失败（退出码 {proc.returncode}）：{err}")
            return answer, len(prompt)


class Handler(BaseHTTPRequestHandler):
    bridge: Bridge = None  # 由 main 注入
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # 安静一点
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status, message):
        self._json(status, {"error": {"message": message, "type": "bridge_error"}})

    def _authorized(self):
        token = self.bridge.args.token
        if not token:
            return True
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {token}" or self.headers.get("x-api-key") == token

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path in ("", "/health"):
            return self._json(200, {"status": "ok", "codex": self.bridge.codex})
        if path.endswith("/models"):
            if not self._authorized():
                return self._error(401, "token 不正确")
            now = int(time.time())
            return self._json(200, {"object": "list", "data": [
                {"id": m, "object": "model", "created": now, "owned_by": "codex-bridge"} for m in MODES
            ]})
        self._error(404, "not found")

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        if not path.endswith("/chat/completions"):
            return self._error(404, "只支持 /v1/chat/completions")
        if not self._authorized():
            return self._error(401, "token 不正确")
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            return self._error(400, f"请求 JSON 无法解析：{e}")

        requested = str(req.get("model") or "codex")
        # 允许 "codex-mentor:gpt-5.5" 这种写法指定底层模型
        mode, _, override = requested.partition(":")
        if mode not in MODES:
            mode = "codex"
        messages = req.get("messages") or []
        if not messages:
            return self._error(400, "messages 为空")

        try:
            answer, prompt_len = self.bridge.run(mode, messages, override or None)
        except subprocess.TimeoutExpired:
            return self._error(504, "codex 响应超时，可用 --timeout 调大")
        except Exception as e:
            log("错误：", e)
            return self._error(502, str(e))

        cid = "chatcmpl-" + uuid.uuid4().hex[:24]
        created = int(time.time())
        usage = {"prompt_tokens": prompt_len // 2, "completion_tokens": len(answer) // 2,
                 "total_tokens": (prompt_len + len(answer)) // 2}

        if req.get("stream"):
            # Codex 一次性返回结果；按 SSE 格式分块发送，兼容只支持流式的插件
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()

            def send(delta, finish=None):
                chunk = {"id": cid, "object": "chat.completion.chunk", "created": created,
                         "model": requested,
                         "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
                self.wfile.write(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode("utf-8"))

            send({"role": "assistant", "content": ""})
            step = 200
            for i in range(0, len(answer), step):
                send({"content": answer[i:i + step]})
            send({}, "stop")
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            self.close_connection = True
            return

        self._json(200, {
            "id": cid, "object": "chat.completion", "created": created, "model": requested,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": answer},
                         "finish_reason": "stop"}],
            "usage": usage,
        })


def main():
    p = argparse.ArgumentParser(description="Zotero <-> Codex 本地桥接（OpenAI 兼容接口）")
    p.add_argument("--host", default="127.0.0.1", help="监听地址，默认仅本机")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--token", default=os.environ.get("ZCB_TOKEN", ""),
                   help="可选：要求插件在 API Key 处填写此值")
    p.add_argument("--workdir", default=os.path.expanduser("~/ScienceMentor"),
                   help="Codex 工作目录，训练记录存在其中的 research-training/judgment-log.md")
    p.add_argument("--codex", default=os.environ.get("CODEX_BIN", ""), help="codex 可执行文件路径")
    p.add_argument("--model", default="", help="可选：指定 Codex 使用的模型")
    p.add_argument("--timeout", type=int, default=600, help="单次请求超时秒数")
    p.add_argument("--max-concurrency", type=int, default=2)
    args = p.parse_args()

    Handler.bridge = Bridge(args)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    log(f"桥接已启动：http://{args.host}:{args.port}/v1")
    log(f"codex: {Handler.bridge.codex}   工作目录: {args.workdir}")
    log("可用模型：" + ", ".join(MODES))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("已停止")


if __name__ == "__main__":
    main()
