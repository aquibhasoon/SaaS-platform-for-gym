import ipaddress
import os

from .models import AuditLog


def _get_trusted_proxy_ips():
    """
    Read trusted reverse-proxy IP addresses from the environment.

    Example:
        TRUSTED_PROXY_IPS=127.0.0.1,10.0.0.10
    """

    value = os.environ.get("TRUSTED_PROXY_IPS", "")

    trusted_ips = set()

    for item in value.split(","):
        item = item.strip()

        if not item:
            continue

        try:
            trusted_ips.add(ipaddress.ip_address(item))
        except ValueError:
            # Ignore invalid configuration values rather than
            # allowing them to affect request handling.
            continue

    return trusted_ips


def _parse_ip(value):
    """
    Return a normalized IP address string or None.
    """

    if not value:
        return None

    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def get_client_ip(request):
    """
    Get the client's IP address safely.

    By default, only REMOTE_ADDR is trusted.

    X-Forwarded-For is considered only when the direct connection
    comes from a proxy explicitly listed in TRUSTED_PROXY_IPS.

    Example:
        TRUSTED_PROXY_IPS=10.0.0.10,127.0.0.1
    """

    if not request:
        return None

    remote_addr = _parse_ip(
        request.META.get("REMOTE_ADDR")
    )

    if not remote_addr:
        return None

    trusted_proxy_ips = _get_trusted_proxy_ips()

    # Only trust X-Forwarded-For when the direct connection
    # is coming from a configured trusted proxy.
    if ipaddress.ip_address(remote_addr) in trusted_proxy_ips:
        forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if forwarded_for:
            # This assumes the trusted reverse proxy is configured
            # to set/overwrite X-Forwarded-For correctly.
            first_ip = forwarded_for.split(",")[0].strip()

            forwarded_ip = _parse_ip(first_ip)

            if forwarded_ip:
                return forwarded_ip

    return remote_addr


def create_audit_log(
    request,
    action,
    description,
    model_name="",
    object_id="",
):
    """
    Create an audit log entry.

    The function is intentionally centralized so all
    application modules use the same logging mechanism.
    """

    user = None

    if (
        request
        and request.user.is_authenticated
    ):
        user = request.user

    return AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else "",
        description=description,
        ip_address=get_client_ip(request),
    )