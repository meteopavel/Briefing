import re
import time
from urllib.parse import quote

import requests

from app.config import GITLAB_AUTHOR_ID, GITLAB_TOKEN, GITLAB_URL, GITLAB_PROJECT_PATH

_cache: dict = {}
_MR_CACHE_TTL = 300  # 5 минут

_BRANCH_SEP_RE = re.compile(r'[-/._]')


class GitLabClient:

    @staticmethod
    def _fetch_all_mrs() -> list[dict]:
        project_encoded = quote(GITLAB_PROJECT_PATH, safe='')
        all_mrs = []
        for page in range(1, 5):
            response = requests.get(
                f'{GITLAB_URL}/api/v4/projects/{project_encoded}/merge_requests',
                headers={'PRIVATE-TOKEN': GITLAB_TOKEN},
                params={
                    'state': 'all',
                    'author_id': GITLAB_AUTHOR_ID,
                    'per_page': 100,
                    'page': page,
                    'order_by': 'updated_at',
                },
                timeout=20,
            )
            response.raise_for_status()
            page_mrs = response.json()
            all_mrs.extend(page_mrs)
            if len(page_mrs) < 100:
                break
        return all_mrs

    @staticmethod
    def _ensure_cache() -> None:
        now = time.monotonic()
        if _cache.get('mrs') is not None and now - _cache.get('ts', 0) < _MR_CACHE_TTL:
            return
        if not GITLAB_URL or not GITLAB_TOKEN or not GITLAB_AUTHOR_ID:
            _cache['mrs'] = []
            _cache['ts'] = now
            return
        _cache['mrs'] = GitLabClient._fetch_all_mrs()
        _cache['ts'] = now

    @staticmethod
    def get_mrs_for_issue(issue_id: int) -> list[dict]:
        """Возвращает список MR, связанных с задачей, по номеру в имени ветки."""
        GitLabClient._ensure_cache()
        id_str = str(issue_id)
        result = []
        for mr in _cache.get('mrs', []):
            branch = mr.get('source_branch', '')
            parts = _BRANCH_SEP_RE.split(branch)
            if id_str not in parts:
                continue
            target = mr.get('target_branch', '')
            if target == 'stage':
                mr_type = 'stage'
            elif target in ('master', 'main'):
                mr_type = 'master'
            else:
                continue  # игнорируем MR в другие ветки
            state = mr.get('state', 'unknown')
            has_conflicts = (
                mr.get('merge_status') == 'cannot_be_merged'
                or mr.get('has_conflicts', False)
            )
            result.append({
                'mr_iid': mr['iid'],
                'url': mr['web_url'],
                'type': mr_type,
                'state': state,
                'has_conflicts': has_conflicts,
            })
        return result

    @staticmethod
    def invalidate_cache() -> None:
        _cache.clear()
