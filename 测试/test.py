#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

def main():
    try:
        with open("/Users/jy_new/项目/2020-12-11.csv", 'a+') as f:
            for i in range(50000):
                f.write("\n17:28:34,使用时长上报,566,578767,27,5091,1499")
    except Exception:
        print("写入数据失败")

main()