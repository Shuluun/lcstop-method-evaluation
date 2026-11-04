"""Read-only lexical adapter for nonstandard numeric JSON constants.
Quoted strings are preserved, including strings crossing blocks. Raw archive unchanged.
Nonfinite numeric tokens become JSON null, never finite values; selected nulls fail eligibility.
"""
import re,io
RX=re.compile(rb'"(?:[^"\\]|\\.)*"|(?P<bad>-?Infinity|NaN)|(?P<open>"(?:[^"\\]|\\.)*\\?$)')
class NumericJSONAdapter(io.RawIOBase):
 def __init__(self,source):self.source=source;self.carry=b'';self.out=b'';self.eof=False;self.replacements=0
 def readable(self):return True
 def _fill(self):
  more=self.source.read(2*1024*1024);data=self.carry+more
  if not more:self.eof=True
  cut=len(data) if self.eof else max(0,len(data)-64)
  chunks=[];start=0
  for m in RX.finditer(data):
   if m.start()>=cut:break
   if m.end()>cut:cut=m.start();break
   if m.lastgroup=='bad':chunks.extend([data[start:m.start()],b'null']);start=m.end();self.replacements+=1
  chunks.append(data[start:cut]);self.out+=b''.join(chunks);self.carry=data[cut:]
  if len(self.carry)>16*1024*1024:raise ValueError('oversized incomplete JSON lexical token')
 def readinto(self,b):
  data=self.read(len(b));b[:len(data)]=data;return len(data)
 def read(self,n=-1):
  if n==0:return b''
  if n<0:raise ValueError('streaming reads only')
  while len(self.out)<n and not self.eof:self._fill()
  ans=self.out[:n];self.out=self.out[n:];return ans