import time
from urllib.parse import quote

import requests

from app.config import GITLAB_TOKEN, GITLAB_URL, GITLAB_PROJECT_PATH

_mr_cache: dict = {}
_MR_CACHE_TTL = 300  # 5 минут


class GitLabClient:

    @staticmethod
    def fetch_mr_status(mr_iid: int) -> dict:
        """Возвращает {state, has_conflicts} для MR. Кэширует на 5 минут."""
        now = time.monotonic()
        cached = _mr_cache.get(mr_iid)
        if cached and now - cached['ts'] < _MR_CACHE_TTL:
            return cached['data']

        if not GITLAB_URL or not GITLAB_TOKEN:
            return {}

        project_encoded = quote(GITLAB_PROJECT_PATH, safe='')
        response = requests.get(
            f'{GITLAB_URL}/api/v4/projects/{project_encoded}/merge_requests/{mr_iid}',
            headers={'PRIVATE-TOKEN': GITLAB_TOKEN},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        result = {
            'state': data.get('state', 'unknown'),
            'has_conflicts': data.get('merge_status') == 'cannot_be_merged' or data.get('has_conflicts', False),
        }
        _mr_cache[mr_iid] = {'data': result, 'ts': now}
        return result
