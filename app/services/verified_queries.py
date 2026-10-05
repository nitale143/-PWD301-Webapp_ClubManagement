"""Small, auditable read tools: no model generates member or task facts."""

import re

from app.models import Task, User
from .access import is_board, require, visible_members
from .assistant import _normalize


def member_query_kind(message):
    text = _normalize(message).strip()
    if re.search(r"^(?:(?:ai oi|hay|giup|toi muon)\s+)*(?:tao|chia|giao|phan cong|de xuat|sua|cap nhat|xoa)\b", text):
        return None
    if any(phrase in text for phrase in ("thong tin", "ho so", "tom tat du lieu")):
        return "member"
    if re.search(r"\b(?:task|cong viec)\b", text) and any(
            phrase in text for phrase in ("cua", "dang lam", "dang co", "liet ke", "xem",
                                         "task gi", "task nao", "cong viec gi")):
        return "tasks"
    return None


def _member(actor, message):
    text = _normalize(message)
    members = visible_members(actor).order_by(User.id).all()
    codes = [row for row in members if re.search(
        r"(?<!\w)" + re.escape(_normalize(row.mssv)) + r"(?!\w)", text)]
    names = [row for row in members if len(_normalize(row.ho_ten)) >= 4 and re.search(
        r"(?<!\w)" + re.escape(_normalize(row.ho_ten)) + r"(?!\w)", text)]
    accented = [row for row in names if row.ho_ten.casefold() in message.casefold()
                and _normalize(row.ho_ten) != row.ho_ten.casefold()]
    if len(codes) > 1 or (codes and names and any(row.id != codes[0].id for row in names)):
        return None
    matches = codes or accented or names
    if not matches and re.search(r"\b(?:toi|minh)\b", text):
        matches = [row for row in members if row.id == actor.id]
    if len(matches) != 1:
        return None
    return matches[0]


def maybe_answer_member_query(actor, message):
    kind = member_query_kind(message)
    if not kind:
        return None
    # These tools do not implement historical or date-filtered membership/tasks.
    if re.search(r"\b20\d{2}\b|\b\d{1,2}/\d{1,2}\b|\b(?:tuan|thang|ky)\s+(?:truoc|sau|nay|\d+)"
                 r"|\b(?:hom nay|hom qua|ngay mai)\b",
                 _normalize(message)):
        return {"intent": "unsupported_query", "provider": "database",
                "verification": "unsupported", "answer":
                "Tra cứu này chưa hỗ trợ lọc theo kỳ hoặc ngày. Bạn có thể xem hồ sơ hiện tại, "
                "task hiện tại của một MSSV, hoặc dùng báo cáo tuần/tháng."}
    member = _member(actor, message)
    if member is None:
        return {"intent": "member_needs_details", "provider": "database",
                "verification": "clarification", "answer":
                "Hãy nêu một MSSV hoặc họ tên chính xác trong phạm vi bạn được xem "
                "(hoặc nói 'của tôi'). Nếu trùng tên, dùng MSSV; tôi chưa đoán người được hỏi."}
    sources = {"user": [member.id]}
    if kind == "member":
        links = sorted(member.ban_links, key=lambda row: row.ban_id)
        bans = ", ".join(link.ban.ten_ban for link in links) or "chưa có ban"
        return {"intent": "member_info", "provider": "database", "verification": "database",
                "sources": sources, "answer":
                f"Hồ sơ hiện tại: {member.ho_ten} ({member.mssv}).\n"
                f"Chức vụ: {member.chuc_vu}; trạng thái tài khoản: {member.status}; ban: {bans}.\n"
                f"Nguồn: user #{member.id} và liên kết ban hiện tại trong database CLB."}
    require(is_board(actor) or member.id == actor.id,
            "Bạn chỉ được xem task của mình hoặc task trong phạm vi BDH quản lý.")
    text = _normalize(message)
    completed = ("hoan thanh" in text or "da xong" in text) and not any(
        phrase in text for phrase in ("chua hoan thanh", "khong hoan thanh", "chua xong"))
    selected = []
    if completed:
        selected.append(("hoan_thanh", "đã hoàn thành"))
    for phrase, state, label in (("dang lam", "dang_lam", "đang làm"),
                                 ("cho duyet", "cho_duyet", "chờ duyệt"),
                                 ("lam lai", "lam_lai", "làm lại")):
        if phrase in text:
            selected.append((state, label))
    if re.search(r"\b(?:da huy|bi huy|task huy|cong viec huy)\b", text):
        selected.append(("huy", "đã hủy"))
    if len(selected) > 1:
        return {"intent": "member_needs_details", "provider": "database",
                "verification": "clarification", "answer":
                "Bạn đang hỏi nhiều trạng thái task. Hãy chọn một trạng thái, "
                "hoặc hỏi 'tất cả task của <MSSV>'."}
    if selected:
        states, label = [selected[0][0]], selected[0][1]
    elif "tat ca" in text and not any(phrase in text for phrase in
            ("chua hoan thanh", "khong hoan thanh", "chua xong")):
        states, label = ["dang_lam", "cho_duyet", "lam_lai", "hoan_thanh", "huy"], "tất cả trạng thái"
    else:
        states, label = ["dang_lam", "cho_duyet", "lam_lai"], "chưa hoàn thành"
    query = Task.query.filter(Task.assignee_id == member.id, Task.trang_thai.in_(states))
    if actor.chuc_vu == "TB" and member.id != actor.id:
        query = query.filter(Task.ban_id.in_(actor.quan_ly_ban_ids()))
    total = query.count()
    tasks = query.order_by(Task.deadline, Task.id).limit(100).all()
    sources["task"] = [row.id for row in tasks]
    lines = [f"Task {label} của {member.ho_ten} ({member.mssv}) trong phạm vi bạn được xem: {total}."]
    lines.extend(f"- #{row.id}: {row.ten_task}; trạng thái {row.trang_thai}; "
                 f"hạn {row.deadline:%d/%m/%Y %H:%M}; sự kiện #{row.event_id}; ban #{row.ban_id}."
                 for row in tasks)
    if total > len(tasks):
        lines.append(f"Đang hiển thị {len(tasks)}/{total} task; xem trang sự kiện để xem toàn bộ.")
    lines.append("Nguồn: task trong database CLB; chưa sửa hoặc giao task nào.")
    return {"intent": "member_tasks", "provider": "database", "verification": "database",
            "sources": sources, "answer": "\n".join(lines)}
