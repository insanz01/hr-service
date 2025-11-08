#!/usr/bin/env python3
import os
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'

import redis
r = redis.from_url('redis://localhost:6379/0', decode_responses=True)
print('Redis keys:', r.keys('job_result:*'))
result = r.get('job_result:49')
print('Result for job 49:', result)