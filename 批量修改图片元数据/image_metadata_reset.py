#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import sys, getopt, os
import re
import pyexiv2

# 修改单个图片元数据
def modify_metadata(image_path, exif, iptc, xmp, is_clear):
    try:
        with open(image_path, 'rb+') as f:
            with pyexiv2.ImageData(f.read()) as img:
                if is_clear:
                    img.clear_exif()
                    img.clear_iptc()
                    img.clear_xmp()
                if exif: img.modify_exif(exif)
                if iptc: img.modify_iptc(iptc)
                if xmp: img.modify_xmp(xmp)
                f.seek(0)
                # 获取图片的字节数据并保存到文件中
                f.write(img.get_bytes())
    except Exception:
        print(image_path,"重置元数据失败")

# 修改指定目录下所有图片元数据
def modify_all_metadata(target_path, exif, iptc, xmp, is_clear):
    all_file_names = os.listdir(target_path)
    for file_name in all_file_names:
        file_path = target_path + "/" + file_name
        if os.path.isdir(file_path): #目录则递归
            modify_all_metadata(file_path, exif, iptc, xmp, is_clear)
        elif re.match(r".*\.(jpg|png)",file_name, re.M|re.I):
            modify_metadata(file_path, exif, iptc, xmp, is_clear)

# 转换参数为字典
def parseParams(value):
    values = value.split("%")
    if len(values) < 2: return None
    result = {}
    for i in range(int(len(values) / 2)):
        result[values[i * 2]] = values[i * 2 + 1] 
    return result

def main(argv):
    inputfile = ''
    exif = ''
    iptc = '' 
    xmp = ''
    clear = False
    try:
        opts, args = getopt.getopt(argv, "hci:e:p:x:")
    except getopt.GetoptError:
        print("接受参数为: -i 目标目录 -c(清除原数据) -e exif元数据(https://www.exiv2.org/metadata.html)，不能带空格如label%我是标签%name%我是名字 -p iptc元数据，同exif -x xmp元数据，同exif")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("接受参数为: -i 目标目录 -c(清除原数据) -e exif元数据(https://www.exiv2.org/metadata.html)，不能带空格如label%我是标签%name%我是名字 -p iptc元数据，同exif -x xmp元数据，同exif")
            sys.exit()
        elif opt == "-i":
            inputfile = arg
        elif opt == "-e":
            exif = arg
        elif opt == "-p":
            iptc = arg
        elif opt == "-x":
            xmp = arg
        elif opt == "-c":
            clear = True
    my_path = os.path.abspath(os.path.dirname(__file__))
    inputfile = os.path.join(my_path, inputfile)
    print ('输入的JSON为：', inputfile)
    print ('设置的exif元数据为：', exif)
    print ('设置的iptc元数据为：', iptc)
    print ('设置的xmp元数据为：', xmp)
    print ("是否清除原数据:", clear)
    # try:
    exif_data = parseParams(exif)
    iptc_data = parseParams(iptc)
    xmp_data = parseParams(xmp)
    modify_all_metadata(inputfile, exif_data, iptc_data, xmp_data, clear)
    print ("已重置为:", exif_data, iptc_data, xmp_data)
    # except Exception:
    #     print ("元数据字典JSON格式错误,重置失败")

if __name__ == "__main__":
    main(sys.argv[1:])