#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import random
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Optional


PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"
SAFARI_WINDOW_ID: Optional[int] = None
GENERIC_TITLE_HINTS = (
    "解读",
    "总结",
    "小结",
    "周报",
    "论文",
    "paper",
)

DEFAULT_BODY_SETTLE_RANGE = (3.5, 7.5)
DEFAULT_TITLE_SETTLE_RANGE = (2.0, 5.0)
DEFAULT_PRE_PUBLISH_RANGE = (12.0, 28.0)
DEFAULT_POST_PUBLISH_RANGE = (45.0, 90.0)


def run_osascript(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-"],
        input=script,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "osascript failed")
    return proc.stdout.strip()


def wait_with_jitter(min_seconds: float, max_seconds: float) -> float:
    if max_seconds < min_seconds:
        raise ValueError(f"Invalid wait range: {min_seconds}..{max_seconds}")
    seconds = random.uniform(min_seconds, max_seconds)
    time.sleep(seconds)
    return seconds


def safari_window_clause() -> str:
    if SAFARI_WINDOW_ID is None:
        return "front window"
    return f'(first window whose id is {SAFARI_WINDOW_ID})'


def safari_js(js: str) -> str:
    escaped = json.dumps(js, ensure_ascii=False)
    script = f'''
tell application "Safari"
  if not (exists {safari_window_clause()}) then error "Safari target window not found"
  return do JavaScript {escaped} in current tab of {safari_window_clause()}
end tell
'''
    return run_osascript(script)


def open_publish_page() -> str:
    script = f'''
tell application "Safari"
  if not (exists {safari_window_clause()}) then error "Safari target window not found"
  set URL of current tab of {safari_window_clause()} to "{PUBLISH_URL}"
  delay 2
  return URL of current tab of {safari_window_clause()}
end tell
'''
    return run_osascript(script)


def get_front_window_id() -> int:
    out = run_osascript(
        '''
tell application "Safari"
  if not (exists front window) then error "Safari front window not found"
  return id of front window
end tell
'''
    )
    return int(out.strip())


def extract_from_markdown(markdown_path: Path) -> tuple[str, str]:
    text = markdown_path.read_text()
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("Markdown must start with a top-level '# ' title")
    title = lines[0][2:].strip()
    body_lines: list[str] = []
    started = False
    for i, line in enumerate(lines):
        if i == 0 and line.startswith("# "):
            started = True
            continue
        if started and line.startswith("# "):
            break
        if started and not line.strip().startswith("!["):
            body_lines.append(line)
    body = "\n".join(body_lines).strip()
    return title, body


def load_body(args: argparse.Namespace) -> tuple[str, str]:
    title = args.title or ""
    body = ""
    if args.markdown:
        md_title, md_body = extract_from_markdown(Path(args.markdown))
        title = title or md_title
        body = md_body
    elif args.body_file:
        body = Path(args.body_file).read_text().strip()
    elif args.body:
        body = args.body.strip()
    else:
        raise ValueError("Provide one of --markdown, --body-file, or --body")
    if not title:
        raise ValueError("A title is required; provide --title or use a markdown file with a top-level title")
    return title.strip(), body.strip()


def body_split_suggestion(body: str) -> str:
    paragraphs = [line.strip() for line in body.splitlines() if line.strip()]
    if len(paragraphs) >= 4:
        pivot = max(2, len(paragraphs) // 2)
        head = " / ".join(paragraphs[:2])
        tail = " / ".join(paragraphs[pivot:pivot + 2])
        return f"Consider splitting into multiple notes, for example part 1 around: {head[:40]} ; part 2 around: {tail[:40]}"
    return "Consider splitting the content into multiple numbered notes such as （一） and （二）."


def title_quality_issue(title: str, body: str) -> Optional[str]:
    stripped = title.strip()
    lowered = stripped.lower()
    if len(stripped) < 6:
        return "Title is too short. It should summarize the note more clearly."
    if any(lowered == hint or lowered.endswith(hint) for hint in GENERIC_TITLE_HINTS):
        return "Title is too generic. Prefer a more specific, content-carrying title."
    if "：" not in stripped and ":" not in stripped and len(stripped) <= 10:
        return "Title is likely too vague. Prefer a title that names the topic and the main idea."
    body_head = "".join(ch for ch in body[:120] if ch not in "\n\r\t ").lower()
    title_head = "".join(ch for ch in stripped if ch not in "\n\r\t ").lower()
    if title_head and title_head in {"论文解读", "本周小结"}:
        return "Title is too generic. Summarize the actual content instead of using a template title."
    if len(body_head) > 30 and stripped.lower() in body_head:
        return "Title appears to repeat the opening body text instead of summarizing the note."
    return None


def validate_inputs(title: str, body: str, cover: Optional[Path]) -> None:
    if cover and not cover.exists():
        raise FileNotFoundError(f"Cover image not found: {cover}")
    if len(title) > 20:
        raise ValueError(f"Title too long for Xiaohongshu ({len(title)} > 20): {title}")
    title_issue = title_quality_issue(title, body)
    if title_issue:
        raise ValueError(f"{title_issue} Current title: {title}")
    if len(body) > 1000:
        raise ValueError(f"Body too long for Xiaohongshu ({len(body)} > 1000). {body_split_suggestion(body)}")


def capture_preview_screenshot(preview_path: Path) -> Path:
    if SAFARI_WINDOW_ID is None:
        raise ValueError("Preview screenshot capture requires --window-id so the correct Safari window stays pinned.")
    script = "/Users/ursula/.codex/skills/snipaste-window-screenshot/scripts/capture_window.py"
    subprocess.run(
        [
            "python3",
            script,
            "--app",
            "Safari",
            "--window-id",
            str(SAFARI_WINDOW_ID),
            "--no-activate",
            "--out",
            str(preview_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return preview_path


def inspect_preview(title: str, body: str) -> dict:
    status = json.loads(
        safari_js(
            textwrap.dedent(
                """
                (() => {
                  const input = Array.from(document.querySelectorAll('input')).find(el => (el.placeholder || '').includes('填写标题'));
                  const editor = document.querySelector('.tiptap.ProseMirror,[contenteditable="true"]');
                  const phonePreview = document.body.innerText.includes('笔记预览');
                  return JSON.stringify({
                    title: input ? (input.value || '') : '',
                    body: editor ? (editor.innerText || '') : '',
                    bodyText: document.body.innerText.slice(0, 5000),
                    phonePreview,
                  });
                })();
                """
            )
        )
    )
    page_title = status.get("title", "")
    page_body = status.get("body", "")
    page_text = status.get("bodyText", "")
    preview_issues: list[str] = []
    if page_title != title:
        preview_issues.append("title-mismatch")
    first_line = next((line for line in body.splitlines() if line.strip()), "")
    if first_line and first_line not in page_body:
        preview_issues.append("body-mismatch")
    if "\\u" in page_text or "\ufffd" in page_text or "��" in page_text:
        preview_issues.append("possible-garbled-text")
    if "  " in page_body:
        preview_issues.append("double-spacing")
    if not status.get("phonePreview"):
        preview_issues.append("phone-preview-missing")
    return {"ok": not preview_issues, "issues": preview_issues, "status": status}


def expect_logged_in() -> None:
    status = json.loads(
        safari_js(
            textwrap.dedent(
                """
                (() => JSON.stringify({
                  url: location.href,
                  text: document.body.innerText.slice(0, 1000)
                }))();
                """
            )
        )
    )
    text = status["text"]
    if "短信登录" in text or "手机号" in text or "发送验证码" in text:
        raise RuntimeError("Creator page is not logged in. Log in to the normal Safari page first.")


def switch_to_image_mode() -> None:
    deadline = time.time() + 12.0
    last_result = {"ok": False, "reason": "timeout"}
    while time.time() < deadline:
        result = json.loads(
            safari_js(
                textwrap.dedent(
                    """
                    (() => {
                      const tabs = Array.from(document.querySelectorAll('.creator-tab'));
                      const visibleTabs = tabs.filter(el => {
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0 && rect.left >= 0 && rect.top >= 0;
                      });
                      let target = visibleTabs.find(el => (el.innerText || '').trim() === '上传图文');
                      if (!target) target = tabs.find(el => (el.innerText || '').trim() === '上传图文');
                      if (!target && visibleTabs.length >= 2) target = visibleTabs[1];
                      if (!target) {
                        return JSON.stringify({
                          ok:false,
                          reason:'no-image-tab',
                          body: document.body.innerText.slice(0, 1000),
                          tabCount: tabs.length
                        });
                      }
                      target.click();
                      target.dispatchEvent(new MouseEvent('click', { bubbles:true, cancelable:true, view:window }));
                      return JSON.stringify({ok:true});
                    })();
                    """
                )
            )
        )
        last_result = result
        if result.get("ok"):
            break
        time.sleep(0.5)
    else:
        raise RuntimeError(f"Failed to switch to image mode: {last_result}")

    deadline = time.time() + 10.0
    while time.time() < deadline:
        status = json.loads(
            safari_js(
                textwrap.dedent(
                    """
                    (() => JSON.stringify({
                      active: Array.from(document.querySelectorAll('.creator-tab.active')).map(el => (el.innerText || '').trim()),
                      body: document.body.innerText.slice(0, 3000),
                      fileInputs: Array.from(document.querySelectorAll('input[type=file]')).map(el => el.accept || '')
                    }))();
                    """
                )
            )
        )
        if "上传图文" in status.get("active", []):
            return
        if "上传图片" in status.get("body", ""):
            return
        if any(".png" in accept or ".jpg" in accept or ".jpeg" in accept for accept in status.get("fileInputs", [])):
            return
        time.sleep(0.5)

    raise RuntimeError(f"Did not reach image upload mode: {status}")


def inject_images(paths: list[Path]) -> None:
    if not paths:
        raise ValueError("At least one image path is required")
    uploads = []
    for path in paths:
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        uploads.append(
            {
                "name": path.name,
                "mime": mime,
                "b64": base64.b64encode(path.read_bytes()).decode("ascii"),
            }
        )
    safari_js("window.__codexUploadB64 = ''; 'ok';")
    payload = json.dumps(uploads, ensure_ascii=False)
    chunk_size = 50000
    for i in range(0, len(payload), chunk_size):
        chunk = payload[i:i + chunk_size]
        safari_js(f"window.__codexUploadB64 += {json.dumps(chunk, ensure_ascii=False)}; 'ok';")
    result = json.loads(
        safari_js(
            f"""
            (() => {{
              const input = document.querySelector('input[type=file][accept*=".jpg"], input[type=file][accept*=".png"], input[type=file]');
              if (!input) return JSON.stringify({{ok:false, reason:'no-file-input'}});
              const payload = window.__codexUploadB64 || '';
              if (!payload) return JSON.stringify({{ok:false, reason:'empty-upload-bytes'}});
              const uploads = JSON.parse(payload);
              const dt = new DataTransfer();
              for (const upload of uploads) {{
                const binary = atob(upload.b64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                dt.items.add(new File([bytes], upload.name, {{ type: upload.mime }}));
              }}
              input.files = dt.files;
              input.dispatchEvent(new Event('input', {{ bubbles:true }}));
              input.dispatchEvent(new Event('change', {{ bubbles:true }}));
              return JSON.stringify({{
                ok:true,
                fileCount: dt.files.length,
                body: document.body.innerText.slice(0, 3000)
              }});
            }})();
            """
        )
    )
    safari_js("window.__codexUploadB64 = ''; 'ok';")
    if not result.get("ok"):
        raise RuntimeError(f"Cover upload did not succeed: {result}")

    deadline = time.time() + 20.0
    while time.time() < deadline:
        status = json.loads(
            safari_js(
                textwrap.dedent(
                    """
                    (() => JSON.stringify({
                      body: document.body.innerText.slice(0, 3000),
                      blobCount: Array.from(document.querySelectorAll('img')).filter(img => (img.src || '').startsWith('blob:')).length
                    }))();
                    """
                )
            )
        )
        if status.get("blobCount", 0) >= len(paths):
            return
        time.sleep(0.5)
    raise RuntimeError(f"Cover upload did not succeed: {status}")


def inject_cover(cover: Path) -> None:
    inject_images([cover])


def generate_text_cover(cover_text: str) -> None:
    step1 = json.loads(
        safari_js(
            f"""
            (() => {{
              const btn = Array.from(document.querySelectorAll('button')).find(el => (el.innerText || '').trim() === '文字配图');
              if (!btn) return JSON.stringify({{ok:false, reason:'no-text2image-btn'}});
              btn.click();
              return JSON.stringify({{ok:true, body: document.body.innerText.slice(0, 2000)}});
            }})();
            """
        )
    )
    if not step1.get("ok"):
        raise RuntimeError(f"Failed to open text2image flow: {step1}")

    deadline = time.time() + 8.0
    while time.time() < deadline:
        status = json.loads(
            safari_js(
                textwrap.dedent(
                    """
                    (() => JSON.stringify({
                      body: document.body.innerText.slice(0, 2000),
                      hasEditor: !!document.querySelector('.tiptap.ProseMirror,[contenteditable="true"]')
                    }))();
                    """
                )
            )
        )
        if "写文字" in status.get("body", "") and status.get("hasEditor"):
            break
        time.sleep(0.5)
    else:
        raise RuntimeError("Text2image editor did not appear")

    step2 = json.loads(
        safari_js(
            f"""
            (() => {{
              const text = {json.dumps(cover_text, ensure_ascii=False)};
              const editor = document.querySelector('.tiptap.ProseMirror,[contenteditable="true"]');
              if (!editor || !editor.editor) return JSON.stringify({{ok:false, reason:'no-text2image-editor'}});
              editor.editor.commands.setContent('<p>' + text.replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c])) + '</p>');
              return JSON.stringify({{ok:true, body: document.body.innerText.slice(0, 2000)}});
            }})();
            """
        )
    )
    if not step2.get("ok"):
        raise RuntimeError(f"Failed to request text-generated cover: {step2}")

    deadline = time.time() + 8.0
    while time.time() < deadline:
        status = json.loads(
            safari_js(
                textwrap.dedent(
                    """
                    (() => {
                      const target = document.querySelector('.edit-text-button') || document.querySelector('.edit-text-button-container');
                      const textNode = document.querySelector('.edit-text-button-text');
                      const editor = document.querySelector('.tiptap.ProseMirror,[contenteditable="true"]');
                      return JSON.stringify({
                        body: document.body.innerText.slice(0, 2000),
                        buttonClass: target ? (target.className || '') : '',
                        buttonTextClass: textNode ? (textNode.className || '') : '',
                        editorText: editor ? (editor.innerText || '') : ''
                      });
                    })();
                    """
                )
        )
        )
        if "disabled" not in status.get("buttonClass", "") and "disabled" not in status.get("buttonTextClass", "") and cover_text in status.get("editorText", ""):
            break
        time.sleep(0.5)
    else:
        raise RuntimeError(f"Text-generated cover button never became ready: {status}")

    click_generate = json.loads(
        safari_js(
            """
            (() => {
              const target = document.querySelector('.edit-text-button') || document.querySelector('.edit-text-button-container');
              if (!target) return JSON.stringify({ok:false, reason:'no-generate-button'});
              const rect = target.getBoundingClientRect();
              const opts = { bubbles:true, cancelable:true, view:window, clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2, button:0, buttons:1 };
              ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(type => {
                const EventCtor = type.startsWith('pointer') ? PointerEvent : MouseEvent;
                target.dispatchEvent(new EventCtor(type, opts));
              });
              return JSON.stringify({ok:true, body: document.body.innerText.slice(0, 2000)});
            })();
            """
        )
    )
    if not click_generate.get("ok"):
        raise RuntimeError(f"Failed to click text-generated cover button: {click_generate}")

    deadline = time.time() + 20.0
    while time.time() < deadline:
        status = json.loads(
            safari_js(
                textwrap.dedent(
                    """
                    (() => JSON.stringify({
                      body: document.body.innerText.slice(0, 3000),
                      url: location.href
                    }))();
                    """
                )
            )
        )
        if "预览图片" in status.get("body", "") and "下一步" in status.get("body", ""):
            break
        time.sleep(1.0)
    else:
        raise RuntimeError("Text-generated cover did not reach preview step")

    deadline = time.time() + 20.0
    while time.time() < deadline:
        click_next = json.loads(
            safari_js(
                """
                (() => {
                  const target = Array.from(document.querySelectorAll('button,div,span')).find(el => (el.innerText || '').trim() === '下一步');
                  if (!target) return JSON.stringify({ok:false, reason:'no-next-button', body: document.body.innerText.slice(0, 2000)});
                  const rect = target.getBoundingClientRect();
                  const opts = { bubbles:true, cancelable:true, view:window, clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2, button:0, buttons:1 };
                  ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(type => {
                    const EventCtor = type.startsWith('pointer') ? PointerEvent : MouseEvent;
                    target.dispatchEvent(new EventCtor(type, opts));
                  });
                  return JSON.stringify({ok:true, body: document.body.innerText.slice(0, 2000)});
                })();
                """
            )
        )
        if not click_next.get("ok") and click_next.get("reason") != "no-next-button":
            raise RuntimeError(f"Failed to confirm text-generated cover: {click_next}")

        status = json.loads(
            safari_js(
                textwrap.dedent(
                    """
                    (() => JSON.stringify({
                      body: document.body.innerText.slice(0, 3000),
                      url: location.href
                    }))();
                    """
                )
            )
        )
        if "图片编辑" in status.get("body", "") and "封面预览" in status.get("body", ""):
            return
        time.sleep(1.5)
    raise RuntimeError("Text-generated cover did not return to image editor")


def wait_for_editor(timeout_sec: float = 8.0) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        result = json.loads(
            safari_js(
                textwrap.dedent(
                    """
                    (() => JSON.stringify({
                      body: document.body.innerText.slice(0, 2000),
                      hasTitle: !!Array.from(document.querySelectorAll('input')).find(el => (el.placeholder || '').includes('填写标题')),
                      hasEditor: !!document.querySelector('.tiptap.ProseMirror,[contenteditable="true"]')
                    }))();
                    """
                )
            )
        )
        if result.get("hasTitle") and result.get("hasEditor") and "图片编辑" in result.get("body", ""):
            return
        time.sleep(0.5)
    raise RuntimeError("Image editor did not appear after cover upload")


def fill_body(body: str) -> None:
    paragraphs = "".join(
        f"<p>{html_escape(line)}</p>" if line else "<p></p>"
        for line in body.split("\n")
    )
    result = json.loads(
        safari_js(
            f"""
            (() => {{
              const editor = document.querySelector('.tiptap.ProseMirror,[contenteditable="true"]');
              if (!editor || !editor.editor) return JSON.stringify({{ok:false, reason:'no-editor'}});
              editor.editor.commands.setContent({json.dumps(paragraphs, ensure_ascii=False)});
              return JSON.stringify({{
                ok:true,
                text: editor.innerText.slice(0, 2000)
              }});
            }})();
            """
        )
    )
    if not result.get("ok") or body.splitlines()[0] not in result.get("text", ""):
        raise RuntimeError(f"Failed to fill body: {result}")


def fill_title(title: str) -> None:
    result = json.loads(
        safari_js(
            f"""
            (() => {{
              const input = Array.from(document.querySelectorAll('input')).find(el => (el.placeholder || '').includes('填写标题'));
              if (!input) return JSON.stringify({{ok:false, reason:'no-title-input'}});
              input.focus();
              input.select();
              document.execCommand('insertText', false, {json.dumps(title, ensure_ascii=False)});
              return JSON.stringify({{
                ok:true,
                value: input.value,
                body: document.body.innerText.slice(0, 3000)
              }});
            }})();
            """
        )
    )
    if not result.get("ok") or result.get("value") != title:
        raise RuntimeError(f"Failed to fill title: {result}")


def click_publish() -> None:
    result = safari_js(
        textwrap.dedent(
            """
            (() => {
              const btn = Array.from(document.querySelectorAll('button,div,span')).find(el => (el.innerText || '').trim() === '发布');
              if (!btn) return JSON.stringify({ok:false, reason:'no-publish'});
              const rect = btn.getBoundingClientRect();
              const opts = { bubbles:true, cancelable:true, view:window, clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2, button:0, buttons:1 };
              ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(type => {
                const EventCtor = type.startsWith('pointer') ? PointerEvent : MouseEvent;
                btn.dispatchEvent(new EventCtor(type, opts));
              });
              return JSON.stringify({ok:true});
            })();
            """
        )
    )
    parsed = json.loads(result)
    if not parsed.get("ok"):
        raise RuntimeError(f"Failed to click publish: {parsed}")


def verify_published(timeout_sec: float = 8.0) -> str:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        status = json.loads(
            safari_js(
                textwrap.dedent(
                    """
                    (() => JSON.stringify({
                      url: location.href,
                      body: document.body.innerText.slice(0, 2000)
                    }))();
                    """
                )
            )
        )
        url = status.get("url", "")
        body = status.get("body", "")
        if "published=true" in url or "/publish/success" in url or "发布成功" in body:
            return status["url"]
        time.sleep(0.5)
    raise RuntimeError("Publish did not complete; success URL not observed")


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title")
    parser.add_argument("--body")
    parser.add_argument("--body-file")
    parser.add_argument("--markdown")
    parser.add_argument("--cover")
    parser.add_argument("--extra-image", action="append", default=[])
    parser.add_argument("--cover-text")
    parser.add_argument("--window-id", type=int)
    parser.add_argument("--print-window-id", action="store_true")
    parser.add_argument("--preview-shot")
    parser.add_argument("--body-settle-min", type=float, default=DEFAULT_BODY_SETTLE_RANGE[0])
    parser.add_argument("--body-settle-max", type=float, default=DEFAULT_BODY_SETTLE_RANGE[1])
    parser.add_argument("--title-settle-min", type=float, default=DEFAULT_TITLE_SETTLE_RANGE[0])
    parser.add_argument("--title-settle-max", type=float, default=DEFAULT_TITLE_SETTLE_RANGE[1])
    parser.add_argument("--pre-publish-min", type=float, default=DEFAULT_PRE_PUBLISH_RANGE[0])
    parser.add_argument("--pre-publish-max", type=float, default=DEFAULT_PRE_PUBLISH_RANGE[1])
    parser.add_argument("--post-publish-min", type=float, default=DEFAULT_POST_PUBLISH_RANGE[0])
    parser.add_argument("--post-publish-max", type=float, default=DEFAULT_POST_PUBLISH_RANGE[1])
    parser.add_argument("--stop-before-publish", action="store_true")
    args = parser.parse_args()

    global SAFARI_WINDOW_ID
    SAFARI_WINDOW_ID = args.window_id
    if args.print_window_id:
        print(get_front_window_id())
        return 0

    title, body = load_body(args)
    cover = Path(args.cover) if args.cover else None
    if not cover and not args.cover_text:
        raise ValueError("Provide --cover for a normal post or --cover-text for a text-generated weekly cover")
    validate_inputs(title, body, cover)

    open_publish_page()
    expect_logged_in()
    switch_to_image_mode()
    if args.cover_text:
        generate_text_cover(args.cover_text)
    else:
        image_paths = [cover] + [Path(path) for path in args.extra_image]
        inject_images(image_paths)
    wait_for_editor()
    fill_body(body)
    body_settle = wait_with_jitter(args.body_settle_min, args.body_settle_max)
    fill_title(title)
    title_settle = wait_with_jitter(args.title_settle_min, args.title_settle_max)
    preview_report = inspect_preview(title, body)
    if not preview_report["ok"]:
        raise RuntimeError(f"Preview inspection failed before publish: {preview_report['issues']}")
    preview_path = None
    if args.preview_shot:
        preview_path = str(capture_preview_screenshot(Path(args.preview_shot)))
    if args.stop_before_publish:
        print(
            json.dumps(
                {
                    "ok": True,
                    "stopped_before_publish": True,
                    "preview": preview_path,
                    "title": title,
                    "body_length": len(body),
                },
                ensure_ascii=False,
            )
        )
        return 0
    pre_publish_wait = wait_with_jitter(args.pre_publish_min, args.pre_publish_max)
    click_publish()
    final_url = verify_published()
    post_publish_wait = wait_with_jitter(args.post_publish_min, args.post_publish_max)
    print(
        json.dumps(
            {
                "ok": True,
                "url": final_url,
                "preview": preview_path,
                "timing": {
                    "body_settle_sec": round(body_settle, 2),
                    "title_settle_sec": round(title_settle, 2),
                    "pre_publish_sec": round(pre_publish_wait, 2),
                    "post_publish_sec": round(post_publish_wait, 2),
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
