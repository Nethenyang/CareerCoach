import subprocess
import json
import time
import random
import os
import sys

# ======================== 配置 ========================
DIRECTIONS = {
    "后端开发": "backend",
    "前端开发": "frontend",
    "算法工程师": "algorithm",
    "数据工程师": "data",
    "全栈开发": "fullstack",
}
CITIES = ["101010100"]
PAGES = [1, 2]
MAX_RETRIES = 1          # 每条详情最多重试 1 次

DATA_FILE = "jd_data.json"
FAILED_FILE = "failed.json"

# 请求间隔（秒）
DELAY_DETAIL = (12, 20)   # 详情之间
DELAY_PAGE = (30, 50)     # 翻页之间
DELAY_DIRECTION = (60, 90)  # 方向之间


# ======================== 工具函数 ========================

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_rate_limited(data):
    """检测是否被 Boss 直聘限流"""
    if not data:
        return False
    err = data.get("error", {})
    msg = err.get("message", "") if isinstance(err, dict) else ""
    return "异常" in msg


def run_bb(cmd):
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", shell=True
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def get_detail(security_id):
    data = run_bb(f'bb-browser site boss/detail "{security_id}" --json')
    if is_rate_limited(data):
        return None, None, True   # 触发限流
    if data and "result" in data:
        jd = data["result"].get("job") or {}
        co = data["result"].get("company") or {}
        return jd, co, False
    return None, None, False      # 其他错误


# ======================== 主流程 ========================

def main():
    # 支持命令行指定方向: python crawl.py 前端开发,数据工程师
    if len(sys.argv) > 1:
        keys = [k.strip() for k in sys.argv[1].split(",")]
        todo = {k: DIRECTIONS[k] for k in keys if k in DIRECTIONS}
        if not todo:
            print(f"未知方向: {sys.argv[1]}")
            print(f"可用: {', '.join(DIRECTIONS.keys())}")
            return
    else:
        todo = dict(DIRECTIONS)

    all_jobs = load_json(DATA_FILE)
    failed = load_json(FAILED_FILE)
    existing_urls = {j.get("source_url", "") for j in all_jobs}

    print(f"已有 {len(all_jobs)} 条数据, {len(failed)} 条失败")
    print(f"本次爬取: {', '.join(todo.keys())}\n")

    for direction_idx, (keyword, direction) in enumerate(todo.items()):
        for city in CITIES:
            for page in PAGES:
                print(f"[{direction_idx+1}/{len(todo)}] {keyword} 第{page}页")

                search_data = run_bb(
                    f'bb-browser site boss/search "{keyword}" --city {city} --page {page} --json'
                )

                if is_rate_limited(search_data):
                    print(f"  ⚠ 搜索触发限流！存盘退出，过几小时再跑。")
                    save_json(DATA_FILE, all_jobs)
                    save_json(FAILED_FILE, failed)
                    return

                if not search_data or "result" not in search_data:
                    print(f"  搜索失败，跳过")
                    continue

                jobs = search_data["result"].get("jobs") or []
                print(f"  搜索到 {len(jobs)} 条")

                new_in_page = 0
                for i, job in enumerate(jobs):
                    security_id = job.get("securityId", "")
                    job_url = job.get("url", "")
                    job_name = job.get("name", "")

                    if job_url and job_url in existing_urls:
                        print(f"    [{i+1}/{len(jobs)}] 跳过(已爬): {job_name}")
                        continue

                    print(f"    [{i+1}/{len(jobs)}] {job_name}")

                    # 获取详情（带一次重试）
                    jd, co, limited = get_detail(security_id)

                    if limited:
                        # 触发限流 → 存盘退出
                        print(f"    ⚠ Boss直聘限流！存盘退出，过几小时再跑。")
                        # 本条记入失败
                        failed.append({"job": job, "securityId": security_id})
                        save_json(DATA_FILE, all_jobs)
                        save_json(FAILED_FILE, failed)
                        return

                    if jd is None:
                        # 非限流错误，重试一次
                        time.sleep(random.randint(20, 30))
                        jd, co, limited = get_detail(security_id)
                        if limited:
                            print(f"    ⚠ Boss直聘限流！存盘退出。")
                            failed.append({"job": job, "securityId": security_id})
                            save_json(DATA_FILE, all_jobs)
                            save_json(FAILED_FILE, failed)
                            return

                    if jd is None:
                        failed.append({"job": job, "securityId": security_id})
                        jd, co = {}, {}

                    record = {
                        "company": job.get("company", ""),
                        "position": job_name,
                        "tier": "",
                        "tech_direction": keyword,
                        "requirements": jd.get("description", ""),
                        "source_url": job_url,
                        "salary": job.get("salary", ""),
                        "experience": job.get("experience", ""),
                        "degree": job.get("degree", ""),
                        "location": jd.get("location", ""),
                        "skills": job.get("skills", []),
                        "company_stage": co.get("stage", ""),
                        "company_scale": co.get("scale", ""),
                        "company_industry": co.get("industry", ""),
                        "company_intro": co.get("intro", ""),
                    }

                    all_jobs.append(record)
                    existing_urls.add(job_url)
                    new_in_page += 1

                    ok = "✓" if record["requirements"] else "✗"
                    n = len(record["requirements"])
                    print(f"      {ok} requirements {n}字")
                    print(f"      等 {random.randint(*DELAY_DETAIL)}s...")
                    time.sleep(random.uniform(*DELAY_DETAIL))

                save_json(DATA_FILE, all_jobs)
                save_json(FAILED_FILE, failed)

                valid = sum(1 for j in all_jobs if j["requirements"])
                print(f"  新增 {new_in_page} | 总计 {len(all_jobs)}(有效 {valid})")

                if page != PAGES[-1]:
                    w = random.uniform(*DELAY_PAGE)
                    print(f"  翻页等 {w:.0f}s...\n")
                    time.sleep(w)

        if direction_idx < len(todo) - 1:
            w = random.uniform(*DELAY_DIRECTION)
            print(f"\n方向完成，等 {w:.0f}s...\n")
            time.sleep(w)

    valid = sum(1 for j in all_jobs if j["requirements"])
    print(f"\n{'='*50}")
    print(f"完成！总计 {len(all_jobs)} 条，有效 {valid} 条")
    if failed:
        print(f"失败 {len(failed)} 条 -> {FAILED_FILE}，下次运行自动重试")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
