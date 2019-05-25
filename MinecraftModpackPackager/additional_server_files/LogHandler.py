
import os
import time
import queue
import threading
import json

class log_handler(object):
	def __init__(self, log_folder=os.path.join(os.path.dirname(os.path.realpath(__file__)),'launcher_logs'), log_max_length=8192, buffer_flush_size=8, number_maxdigits=8):
		self.log_time = time.time()
		self.log_time_str = time.strftime('%Y_%m_%d__%H_%M_%S', time.gmtime(self.log_time))
		self.log_dir = os.path.join(log_folder, self.log_time_str)
		self.log_id = 0
		self.log_length = 0
		self.log_max_length = log_max_length
		self.buffer_flush_size = buffer_flush_size
		self.number_maxdigits = number_maxdigits
		self.log_queue_lock = threading.RLock()
		self.log_queue = queue.Queue()
		self.stop_event = threading.Event()
		os.makedirs(self.log_dir)
		self.auto_flush_async()
	
	def auto_flush(self):
		while not self.stop_event.is_set():
			self.flush()
			time.sleep(1)
	
	def auto_flush_async(self):
		self.auto_flush_thr = threading.Thread(target=self.auto_flush, daemon=True)
		self.auto_flush_thr.start()
	
	def stop(self):
		self.stop_event.set()
		self.auto_flush_thr.join(timeout=120)
		self.flush()
		with self.log_queue_lock:
			self.translate_log(self.log_id)
	
	def translate_log(self, log_id):
		with open(os.path.join(self.log_dir, '{}.jsonl'.format(str(log_id).zfill(self.number_maxdigits))), 'r') as l_fp:
			with open(os.path.join(self.log_dir, '{}.json'.format(str(log_id).zfill(self.number_maxdigits))), 'wb') as j_fp:
				j_fp.write(b'[\r\n')
				is_first = True
				for l in l_fp:
					if is_first:
						is_first = False
					else:
						j_fp.write(b',\r\n')
					j_fp.write(l.replace('\r\n','').replace('\n','').encode('utf-8'))
				j_fp.write(b'\r\n]\r\n')

	def flush(self):
		with self.log_queue_lock:
			while not self.log_queue.empty():
				prev_id = self.log_id
				with open(os.path.join(self.log_dir, '{}.jsonl'.format(str(self.log_id).zfill(self.number_maxdigits))), 'ab') as fp:
					while not self.log_queue.empty():
						log_dat = self.log_queue.get()
						log_json = json.dumps(log_dat).replace('\r\n','').replace('\n','')
						fp.write(log_json.encode('utf-8'))
						fp.write(b'\r\n')
						self.log_length = self.log_length + 1
						if self.log_length >= self.log_max_length:
							self.log_id = self.log_id + 1
							self.log_length = 0
							break
				if prev_id != self.log_id:
					self.translate_log(prev_id)
	
	def load_lognum(self, num, rng=None):
		jsonl_fname = os.path.join(self.log_dir, '{}.jsonl'.format(str(num).zfill(self.number_maxdigits)))
		json_fname = os.path.join(self.log_dir, '{}.json'.format(str(num).zfill(self.number_maxdigits)))
		if num >= self.log_id and not os.path.isfile(jsonl_fname):
			self.flush()
		if os.path.isfile(json_fname):
			print(rng)
			with open(json_fname, 'r') as fp:
				ret = json.load(fp)
				if rng is None:
					return ret
				else:
					return ret[rng[0]:rng[1]]
		elif os.path.isfile(jsonl_fname):
			with open(jsonl_fname, 'r') as fp:
				lineno = 0
				ret = []
				for line in fp:
					if (rng is None) or (rng[0] is None) or (lineno >= rng[0]):
						ret.append(json.loads(line))
					if (not rng is None) and (not rng[1] is None) and (lineno >= rng[1]):
						return ret
					lineno = lineno + 1
				return ret
		else:
			return []
	
	def load_logrange(self, rng=None):
		if rng is None:
			rng = (0,self.log_id*self.log_max_length+self.log_length)
		start_pos = int(rng[0] % self.log_max_length)
		start_id = int(rng[0] / self.log_max_length)
		end_pos = int(rng[1] % self.log_max_length)
		end_id = int(rng[1] / self.log_max_length)
		print(start_pos, start_id, end_pos, end_id)
		if start_id==end_id:
			return self.load_lognum(start_id, rng=(start_pos, end_pos))
		else:
			ret = self.load_lognum(start_id, rng=(start_pos, None))
			for i in range(start_pos+1,end_pos):
				ret = ret + self.load_lognum(i)
			ret = ret + self.load_lognum(end_id, rng=(None, end_pos))
			return ret
	
	def add_str(self, string, is_err=False):
		self.log_queue.put(self.parse_str(string, is_err=is_err))
		if self.log_queue.qsize() >= self.buffer_flush_size:
			self.flush()
	
	def parse_str(self, string, is_err=False):
		unixtime = time.time()
		parts = string.split(': ',1)
		if len(parts)>=2:
			head, body = parts
		else:
			head = ''
			body = string
		time_str = time.strftime('%H:%M:%S', time.localtime(unixtime))
		thread = None
		log_type = None
		component = None
		if head!='':
			head_parts = [p.replace('[','').replace(']','') for p in head.split('] [')]
			part_no = 0
			for part in head_parts:
				if part_no==0:
					time_str = part
				elif part_no==1:
					part_split = part.split('/')
					if len(parts)>=2:
						thread, log_type = part_split
					else:
						thread = ''
						log_type = part
				elif part_no==2:
					component = part.split('/')
				elif part_no > 2:
					component = component + part.split('/')
				part_no = part_no + 1
		return {
			'unixtime':unixtime,
			'raw':string,
			'is_err':is_err,
			'time_str':time_str,
			'thread':thread,
			'log_type':log_type,
			'component':component,
			'text':body,
		}
