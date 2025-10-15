"""
Assign two users to the same group.

Usage:
    python manage.py shell < backend/scripts/add_users_to_group.py
"""

from django.contrib.auth import get_user_model

from groups.models import Group, GroupMember

User = get_user_model()

GROUP_ID = "BTF999"
GROUP_DEFAULTS = {
    "name": "BTF999",
    "track": "AUS-NSW",
    "status": "active",
}

USER_EMAILS = [
    "gss10282007@gmail.com",
    "gss10282007@126.com",
]

def ensure_user(email: str) -> User:
    """
    Fetch the user by email. If absent, create a basic account so the
    group assignment can proceed.
    """
    user = User.objects.filter(email=email).first()
    if user:
        return user

    print(f"[info] User '{email}' 不存在，正在创建一个临时账户。")
    user = User(email=email, username=email)
    user.set_unusable_password()
    user.role = user.role or "student"
    user.save()
    return user


def ensure_group(group_id: str) -> Group:
    """
    Fetch or create the group that should contain the users.
    """
    group, created = Group.objects.get_or_create(
        id=group_id,
        defaults=GROUP_DEFAULTS,
    )
    if created:
        print(f"[info] 已创建群组 {group_id}")
    return group


def main() -> None:
    group = ensure_group(GROUP_ID)

    for email in USER_EMAILS:
        user = ensure_user(email)
        membership, created = GroupMember.objects.get_or_create(
            group=group,
            user=user,
            defaults={"role": "student"},
        )
        if created:
            print(f"[ok] 已将 {email} 加入群组 {group.id}")
        else:
            print(f"[skip] {email} 已在群组 {group.id} 中，跳过。")

    print("[done] 操作完成。如脚本新建了用户，其密码处于不可用状态，只能通过验证码登录。")


if __name__ == "__main__":
    main()
