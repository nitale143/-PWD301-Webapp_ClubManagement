"""Shared shell metadata. Never seeds sample data or impersonates a role."""
from flask import request
from flask_login import current_user
from app.models import Notification
from app.services.common import club_now


def workspace_context():
    endpoint = request.endpoint or ""
    labels = {"main.home": ("Tổng quan câu lạc bộ", "Theo dõi và phối hợp hoạt động FIA."),
              "main.tasks": ("Công việc", "Cùng theo dõi các đầu việc của câu lạc bộ."),
              "member": ("Thành viên", "Kết nối, quản lý và phát triển đội ngũ FIA."),
              "event": ("Sự kiện FIA", "Cùng nhau tạo nên những hoạt động đáng nhớ."),
              "funds": ("Quỹ câu lạc bộ", "Minh bạch khoản thu, chi và tình trạng đóng quỹ."),
              "ai": ("AI Agent", "Trợ lý cho công việc câu lạc bộ, có kiểm chứng và phê duyệt."),
              "admin.approve_list": ("Phê duyệt thành viên", "Chào đón những thành viên mới của FIA."),
              "admin.role_list": ("Vai trò & phân quyền", "Phối hợp và phân công trách nhiệm trong câu lạc bộ."),
              "profile": ("Hồ sơ cá nhân", "Thông tin và hoạt động của thành viên.")}
    title, subtitle = labels.get(endpoint, labels.get(endpoint.split(".")[0], ("FIA Workspace", "")))
    approved = current_user.is_authenticated and current_user.status == "approved"
    notifications = (Notification.query.filter_by(user_id=current_user.id)
                     .order_by(Notification.thoi_gian.desc()).limit(8).all()) if approved else []
    now = club_now()
    return {"workspace_title": title, "workspace_subtitle": subtitle,
            "workspace_today": now, "current_time": now, "shell_notifications": notifications,
            "shell_unread": sum(not item.da_doc for item in notifications)}
