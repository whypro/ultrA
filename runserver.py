# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
import os
# 将依赖模块文件夹加入系统路径
deps_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'deps')
sys.path.insert(0, deps_path)

from ultrA import create_app

app = create_app('ultrA.config')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
