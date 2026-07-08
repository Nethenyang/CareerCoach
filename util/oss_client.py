import oss2
from core.config import settings

"""
阿里云 OSS 客户端：上传、下载、删除、预签名 URL
"""
# ── OSS 认证与 Bucket 实例 ──
_auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
_bucket = oss2.Bucket(_auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)

# ── 上传文件 ──
def upload_file(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """上传文件到 OSS，返回文件访问 URL"""
    _bucket.put_object(key, data, headers={"Content-Type": content_type})
    return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{key}"

# ── 下载文件 ──
def download_file(key: str) -> bytes:
    """从 OSS 下载文件内容"""
    result = _bucket.get_object(key)
    return result.read()

# ── 删除文件 ──
def delete_file(key: str) -> None:
    """删除 OSS 上的文件"""
    _bucket.delete_object(key)

# ── 从 URL 提取 OSS Key ──
def extract_key(url: str) -> str:
    """从完整的 OSS URL 中提取 object key"""
    prefix = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/"
    if url.startswith(prefix):
        return url[len(prefix):]
    return url

# ── 生成预签名 URL ──
def presigned_url(key: str, expires: int = 3600) -> str:
    """生成临时访问链接，默认有效期 1 小时"""
    return _bucket.sign_url("GET", key, expires)