# ==================================================================================================
# Copyright 2011 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

import re
from twitter.common.lang import Compatibility

from twitter.common.collections import OrderedDict

class Properties(object):
  """
    A Python reader for java.util.Properties formatted data as oulined here:
    http://download.oracle.com/javase/6/docs/api/java/util/Properties.html#load(java.io.Reader)
  """

  @staticmethod
  def load(data):
    """
      Loads properties from an open stream or the contents of a string and returns a dict of the
      parsed property data.
    """

    if hasattr(data, 'read') and callable(data.read):
      contents = data.read()
    elif isinstance(data, Compatibility.string):
      contents = data
    else:
      raise TypeError('Can only process data from a string or a readable object, given: %s' % data)

    return Properties._parse(contents.splitlines())


  # An unescaped '=' or ':' forms an explicit separator
  _EXPLICIT_KV_SEP = re.compile(r'(?<!\\)[=:]')


  @staticmethod
  def _parse(lines):
    def coalesce_lines():
      line_iter = iter(lines)
      try:
        buffer = ''
        while True:
          line = next(line_iter)
          if line.strip().endswith('\\'):
            # Continuation.
            buffer += line.strip()[:-1]
          else:
            if buffer:
              # Continuation join, preserve left hand ws (could be a kv separator)
              buffer += line.rstrip()
            else:
              # Plain old line
              buffer = line.strip()

            try:
              yield buffer
            finally:
              buffer = ''
      except StopIteration:
        pass

    def normalize(atom):
      return re.sub(r'\\([:=\s])', r'\1', atom.strip())

    def parse_line(line):
      if line and not (line.startswith('#') or line.startswith('!')):
        match = Properties._EXPLICIT_KV_SEP.search(line)
        if match:
          return normalize(line[:match.start()]), normalize(line[match.end():])
        else:
          space_sep = line.find(' ')
          if space_sep == -1:
            return normalize(line), ''
          else:
            return normalize(line[:space_sep]), normalize(line[space_sep:])

    props = OrderedDict()
    for line in coalesce_lines():
      kv_pair = parse_line(line)
      if kv_pair:
        key, value = kv_pair
        props[key] = value
    return props

  @staticmethod
  def dump(props, output):
    """Dumps a dict of properties to the specified open stream or file path."""
    def escape(token):
      return re.sub(r'([=:\s])', r'\\\1', token)

    def write(out):
      for k, v in props.items():
        out.write('%s=%s\n' % (escape(str(k)), escape(str(v))))

    if hasattr(output, 'write') and callable(output.write):
      write(output)
    elif isinstance(output, Compatibility.string):
      with open(output, 'w+a') as out:
        write(out)
    else:
      raise TypeError('Can only dump data to a path or a writable object, given: %s' % output)
