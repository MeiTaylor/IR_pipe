import re
import json
from dateutil.parser import parse
from datetime import datetime

def process_newness(file_path):

    def extract_date_from_snippet(snippet):
        match = re.search(r'(\b\w+\b \d{1,2}, \d{4})', snippet)
        if match:
            try:
                date = parse(match.group(1), fuzzy=True).date()
                return date
            except ValueError:
                return None
        return None

    def extract_date_from_metatags(metatags):
        date_keys = ['article:published_time', 'sort_date']
        for tag in metatags:
            for key in date_keys:
                if key in tag:
                    date_str = tag[key]
                    try:
                        date = parse(date_str, fuzzy=True).date()
                        return date
                    except ValueError:
                        pass
        return None

    def extract_dates_from_items(items):
        evidence_dates = {}
        for item in items:
            for evidence_key, evidence in item.items():
                # 提取 snippet 中的时间信息
                snippet = evidence.get('snippet', '')
                date_from_snippet = extract_date_from_snippet(snippet)
                if date_from_snippet:
                    evidence_dates[evidence_key] = date_from_snippet
                    continue

                # 提取 metatags 中的时间信息
                pagemap = evidence.get('pagemap', {})
                metatags = pagemap.get('metatags', [])
                date_from_metatags = extract_date_from_metatags(metatags)
                if date_from_metatags:
                    evidence_dates[evidence_key] = date_from_metatags
                    continue

                # 默认日期为None
                evidence_dates[evidence_key] = None

        return evidence_dates

    def score_by_time_gradient(dates):
        now = datetime.now().date()
        gradients = [7, 15, 30, 90, 180, 365, 730]  # 以天为单位的梯度：一星期、半个月、30天、90天、半年、1年、两年
        scores = {}
        for evidence_key, date in dates.items():
            if date is None:
                scores[evidence_key] = 0
            else:
                diff_days = (now - date).days
                score = 1  # 默认为1分
                for i, gradient in enumerate(gradients):
                    if diff_days <= gradient:
                        score = 10 - i
                        break
                scores[evidence_key] = score
        return scores

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = data.get('items', [])
        evidence_dates = extract_dates_from_items(items)
        scores = score_by_time_gradient(evidence_dates)

        # 将日期和分数添加到 evidence 中
        for item in items:
            for evidence_key, evidence in item.items():
                date = evidence_dates.get(evidence_key, None)
                evidence['Newness'] = {
                    'Date': date.isoformat() if date else 'No date found',
                    'NewnessScore': scores.get(evidence_key, 0)
                }

        # 将修改后的数据写回到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Processed {file_path} successfully.")
        return True

    except (json.JSONDecodeError, KeyError, IOError) as e:
        print(f"Failed to process {file_path}: {e}")
        return False



# 示例调用
file_path = r'/workspaces/com_pipe/Query 2.json'
process_newness(file_path)
