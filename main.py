from __future__ import annotations

from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from db.couchbase_client import repo
from config.app_cfg import (
    CB_BUCKET, CB_SCOPE, CB_COLLECTION,
    DEFAULT_THREAD_ID, API_HOST, API_PORT
)

app = FastAPI(title="Couchbase Comments Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup():
    repo.connect()


class CreateCommentIn(BaseModel):
    author: str = Field(min_length=1, max_length=60)
    text: str = Field(min_length=1, max_length=5000)
    parent_id: Optional[str] = None
    thread_id: str = DEFAULT_THREAD_ID


class CommentOut(BaseModel):
    id: str
    thread_id: str
    parent_id: Optional[str]
    author: str
    text: str
    created_at: str
    depth: int
    path: List[str]
    children: List["CommentOut"] = []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_comment_id() -> str:
    return f"comment::{uuid4()}"


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/comments", response_model=Dict[str, Any])
def create_comment(payload: CreateCommentIn):
    parent_doc = None
    if payload.parent_id:
        try:
            parent_doc = repo.get(payload.parent_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Parent comment not found")

        if parent_doc.get("type") != "comment":
            raise HTTPException(status_code=400, detail="Parent is not a comment")
        if parent_doc.get("thread_id") != payload.thread_id:
            raise HTTPException(status_code=400, detail="Parent belongs to another thread")

    comment_id = _make_comment_id()
    created_at = _now_iso()

    if parent_doc:
        path = list(parent_doc.get("path", [])) + [payload.parent_id]
        depth = int(parent_doc.get("depth", 0)) + 1
    else:
        path = []
        depth = 0

    doc = {
        "type": "comment",
        "id": comment_id,
        "thread_id": payload.thread_id,
        "parent_id": payload.parent_id,
        "author": payload.author,
        "text": payload.text,
        "created_at": created_at,
        "path": path,
        "depth": depth,
    }

    repo.upsert(comment_id, doc)
    return doc


@app.get("/api/comments/tree", response_model=List[CommentOut])
def get_comments_tree(thread_id: str = DEFAULT_THREAD_ID):
    stmt = f"""
    SELECT c.*
    FROM `{CB_BUCKET}`.`{CB_SCOPE}`.`{CB_COLLECTION}` AS c
    WHERE c.type = "comment" AND c.thread_id = $thread_id
    ORDER BY c.created_at ASC
    """
    rows = repo.query(stmt, {"thread_id": thread_id})

    by_id: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        by_id[r["id"]] = {**r, "children": []}

    roots: List[Dict[str, Any]] = []
    for _, node in by_id.items():
        pid = node.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(node)
        else:
            roots.append(node)

    return roots


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)