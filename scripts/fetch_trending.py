#!/usr/bin/env python3
"""抓取 GitHub Trending，存 JSON + 归档历史快照 + 更新索引 + 通知 Server酱。

用法：
  python fetch_trending.py auto        # 自动判断：每天daily，周一加weekly，月初加monthly
  python fetch_trending.py weekly      # 只抓指定时段
"""
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_DIR, 'data')
HISTORY_DIR = os.path.join(DATA_DIR, 'history')
INDEX_FILE = os.path.join(HISTORY_DIR, 'index.json')

TRENDING_URL = 'https://github.com/trending?since={period}'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; trending-fetcher/1.0)'}


def fetch_html(period):
    url = TRENDING_URL.format(period=period)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')


def parse_trending(html):
    items = []
    articles = re.findall(r'<article class="Box-row">(.*?)</article>', html, re.DOTALL)
    for i, art in enumerate(articles, 1):
        repo_match = re.search(r'<h2[^>]*>.*?<a[^>]*href="(/[^"]+)"', art, re.DOTALL)
        repo = repo_match.group(1).strip('/') if repo_match else ''

        desc_match = re.search(r'<p class="col-9[^"]*"[^>]*>(.*?)</p>', art, re.DOTALL)
        desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip() if desc_match else ''

        lang_match = re.search(r'<span itemprop="programmingLanguage">([^<]+)</span>', art)
        lang = lang_match.group(1).strip() if lang_match else ''

        total_match = re.search(r'href="/[^"]+/stargazers"[^>]*>\s*([\d,]+)\s*</a>', art)
        stars_total = int(total_match.group(1).replace(',', '')) if total_match else 0

        forks_match = re.search(r'href="/[^"]+/forks"[^>]*>\s*([\d,]+)\s*</a>', art)
        forks = int(forks_match.group(1).replace(',', '')) if forks_match else 0

        period_match = re.search(r'([\d,]+)\s*stars?\s*(?:today|this week|this month)', art)
        stars_period = int(period_match.group(1).replace(',', '')) if period_match else 0

        if repo:
            items.append({
                'rank': i,
                'repo': repo,
                'description': desc,
                'language': lang,
                'stars_period': stars_period,
                'stars_total': stars_total,
                'forks': forks,
                'url': f'https://github.com/{repo}',
                'fetched_at': datetime.now(timezone.utc).isoformat()
            })
    return items


def save_current(period, data):
    path = os.path.join(DATA_DIR, f'{period}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def archive(period, data, date_str):
    dir_path = os.path.join(HISTORY_DIR, period)
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, f'{date_str}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_index(period, date_str):
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index = json.load(f)
    else:
        index = {'daily': [], 'weekly': [], 'monthly': []}
    for k in ('daily', 'weekly', 'monthly'):
        index.setdefault(k, [])
    if date_str not in index[period]:
        index[period].insert(0, date_str)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def notify_serverchan(period, data):
    key = os.environ.get('SERVERCHAN_KEY', '')
    if not key:
        print('SERVERCHAN_KEY 未配置，跳过通知')
        return
    title = f'GitHub {period} 热榜更新（Top3）'
    top3 = '\n'.join(f'{i+1}. {d["repo"]} (+{d["stars_period"]})' for i, d in enumerate(data[:3]))
    desp = f'本期 GitHub Trending Top3:\n\n{top3}\n\n共 {len(data)} 个项目已更新。\n\n[查看完整榜单](https://github.com/OWNER/trending-web)'
    payload = urllib.parse.urlencode({'title': title, 'desp': desp}).encode()
    try:
        req = urllib.request.Request(f'https://sctapi.ftqq.com/{key}.send', data=payload)
        urllib.request.urlopen(req, timeout=10)
        print('Server酱通知已发送')
    except Exception as e:
        print(f'通知发送失败: {e}')


def run(period):
    print(f'--- 抓取 {period} ---')
    html = fetch_html(period)
    data = parse_trending(html)
    print(f'解析到 {len(data)} 个项目')
    if not data:
        print('无数据，跳过')
        return
    save_current(period, data)
    beijing_now = datetime.now(timezone(timedelta(hours=8)))
    date_str = beijing_now.strftime('%Y-%m-%d')
    archive(period, data, date_str)
    update_index(period, date_str)
    print(f'已存 {period}.json + 归档 history/{period}/{date_str}.json')
    if period == 'weekly':
        notify_serverchan(period, data)


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else 'auto'
    if arg == 'auto':
        beijing_now = datetime.now(timezone(timedelta(hours=8)))
        run('daily')
        if beijing_now.weekday() == 0:
            run('weekly')
        if beijing_now.day == 1:
            run('monthly')
    else:
        run(arg)
