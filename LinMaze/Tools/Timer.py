import time

class Timer(object):
	def __init__(self, length=0):
		self.length = length
		self.until = time.time()+self.length
	
	def __str__(self):
		return "%5.2f sec" %(self.until-time.time())
		
	def is_running(self):
		return time.time() < self.until
	
	def set(self, length):
		self.length = length
		
	def reset(self):
		self.until = time.time()+self.length