#!/usr/bin/env python3

#TODO: add graphical logger UI

import os
import sys
import time
import subprocess
import threading
import queue

import settings
import setup
import LogHandler

def fp_to_line_queue(fp, thread_name=None):
	def fp_reader(fp, out_queue):
		for line in fp:
			out_queue.put(line)
	out_queue = queue.Queue(maxsize=256)
	read_thread = threading.Thread(target=fp_reader, args=(fp, out_queue), daemon=True, name=thread_name)
	read_thread.start()
	return out_queue, read_thread

class server_starter(object):
	def __init__(self, server_settings=settings.server_settings, run_dir=os.path.dirname(os.path.realpath(__file__)), log_handler=None):
		self.server_settings = server_settings
		self.run_dir = run_dir
		self.in_queue = None
		self.in_q_thr = None
		self.stop_event = threading.Event()
		self.running_server_event = threading.Event()
		self.processing_input_event = threading.Event()
		self.log_handler = log_handler
		if self.log_handler is None:
			self.log_handler = LogHandler.log_handler()
	
	def run_server(self):
		# set state event to indicate server is running
		self.running_server_event.set()
		# generate command to run the server
		command = [self.server_settings.javacmd, '-server', '-Xmx{}'.format(self.server_settings.max_ram), ] + self.server_settings.java_parameters + ['-jar', self.server_settings.forgejar, 'nogui']
		# start server process
		proc = subprocess.Popen(
			command, 
			stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, 
			cwd=self.run_dir, 
		)
		# generate queues to handle the output and stderr of the program
		out_queue, out_q_thr = fp_to_line_queue(proc.stdout)
		err_queue, err_q_thr = fp_to_line_queue(proc.stderr)
		# if input not being captured, generate queue to handle user input
		if self.in_queue is None:
			self.in_queue, self.in_q_thr = fp_to_line_queue(sys.stdin)
		# clear the user input queue
		while not self.in_queue.empty():
			try:
				self.in_queue.get_nowait()
			except queue.Empty:
				pass
		# set state event to indicate input queue is being processed
		self.processing_input_event.set()
		# loop until process exits and both output queues are complete
		while proc.poll() is None or out_q_thr.is_alive() or err_q_thr.is_alive() or not out_queue.empty() or not err_queue.empty():
			out_empty = False
			err_empty = False
			in_empty = False
			try:
				# get a stdout line and log it
				out = out_queue.get_nowait().decode('utf-8')
				sys.stdout.write(out)
				self.log_handler.add_str(out)
			except queue.Empty:
				# if stdout queue is empty, mark that down
				out_empty = True
			try:
				# get a stderr line and log it as an error
				err = err_queue.get_nowait().decode('utf-8')
				sys.stderr.write(err)
				self.log_handler.add_str(err, is_err=True)
			except queue.Empty:
				# if stderr queue is empty, mark that down
				err_empty = True
			try:
				# get a stdin line and send it to the server process
				line = self.in_queue.get_nowait().encode('utf-8')
				proc.stdin.write(line)
				proc.stdin.flush()
			except queue.Empty:
				# if stdin queue is empty, mark that down
				in_empty = True
			# if all queues are empty, delay for a little bit to let the buffer fill back up
			if out_empty and err_empty and in_empty:
				time.sleep(0.005)
		# clear state events to indicate server is no longer running
		self.processing_input_event.clear()
		self.running_server_event.clear()
		# return the exit code of the server process
		return proc.returncode
	
	def run_server_repeatedly(self):
		print("Starting server")
		while not self.stop_event.is_set():
			exit_code = self.run_server()
			print("Server process finished")
			print("The exit code was: {}".format(exit_code))
			try:
				print("If you want to completely stop the server process now, press Ctrl+C before the time is up!")
				wait_start_time=time.time()
				wait_end_time = wait_start_time + 11
				while (wait_end_time-time.time())>0:
					sys.stdout.write("\rRestarting server in {} ".format(int(wait_end_time-time.time())))
					time.sleep(0.1)
				print('')
			except KeyboardInterrupt:
				print('')
				self.log_handler.stop()
				print("Exiting...")
				self.stop_event.set()
			if not self.stop_event.is_set():
				print("Rebooting now!")

	def run(self):
		# run download script if files are missing
		if not setup.check_files(run_dir=self.run_dir):
			print("Missing required jars. Running install script!")
			setup.dl_files(run_dir=self.run_dir)
		# make sure eula is agreed to
		setup.check_eula(run_dir=self.run_dir)

		# run the server until it is forcefully closed!
		self.run_server_repeatedly()
	
	def stop(self):
		# set flag that the server shouldn't be restarted
		self.stop_event.set()
		# if server is running, send a "stop" command to it
		if self.running_server_event.wait(timeout=1): # using wait with 1 second timeout to prevent race condition
			# wait to confirm that our input will not be cleared after sending
			while not self.processing_input_event.wait(timeout=10):
				# if server is not running, must have exited since our last check, so can safely continue
				if not self.running_server_event.is_set():
					break
			# check that input is definitely still being processed before sending it
			if self.processing_input_event.is_set():
				#send stop command to the server
				self.in_queue.put('stop\n')

def main(log_handler=None):
	server_starter(server_settings=settings.server_settings, log_handler=log_handler).run()

if __name__=="__main__":
	main()
