import os,sys,socket,subprocess,time,struct,json
if len(sys.argv)>1:
 s=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);s.bind(sys.argv[1]+'.net')
 with open('/tmp/flipper-key-events.jsonl','w',buffering=1) as f:
  while True:f.write(s.recv(512).decode()+'\n')
else:
 fifo='/tmp/flipper-key-test';os.mkfifo(fifo)
 env=dict(os.environ,LV_LINUX_KEYBOARD_DEVICE=fifo)
 app=subprocess.Popen(['/usr/share/APPLaunch/apps/flipper-one-remote/flipper-one-remote',__file__],env=env)
 try:
  time.sleep(.5);f=os.open(fifo,os.O_WRONLY|os.O_NONBLOCK)
  for code in [5,6,7,8,9,28,14,103,108,105,106,23,36,37,38,15,33,45,44,46,1]:
   for v in [1,0]:os.write(f,struct.pack('llHHi',0,0,1,code,v));time.sleep(.03)
  time.sleep(.3)
  events=[json.loads(line) for line in open('/tmp/flipper-key-events.jsonl')]
  expected=['esc','view','power','edit','run','ok','back','up','down','left','right','up','left','down','right','appsw','up','down','left','right','back']
  assert events==[{'key':key,'down':state} for key in expected for state in [True,False]],events
  print('PASS: 21 mapped keys, all press/release events')
  os.write(f,struct.pack('llHHi',0,0,1,1,1));app.wait(timeout=3)
  print('PASS: long Escape clean exit')
 finally:
  if app.poll() is None:app.terminate();app.wait()
  os.unlink(fifo)
