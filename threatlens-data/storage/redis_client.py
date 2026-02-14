import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def test_redis():
    r.set("test", "hello redis", ex=60)
    value = r.get("test")
    print(f"✅ Redis OK: {value}")

test_redis()
