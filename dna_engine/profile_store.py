import redis
import json
from datetime import datetime

class DNAProfileStore:
    def __init__(self, host="localhost", port=6379):
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True
        )

    def _key(self, entity_type, entity_id):
        return f"dna:{entity_type}:{entity_id}"

    def get_profile(self, entity_type, entity_id):
        key = self._key(entity_type, entity_id)
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def save_profile(self, entity_type, entity_id, profile):
        key = self._key(entity_type, entity_id)
        profile["last_updated"] = datetime.utcnow().isoformat()
        self.client.set(key, json.dumps(profile))

    def profile_exists(self, entity_type, entity_id):
        key = self._key(entity_type, entity_id)
        return self.client.exists(key)
