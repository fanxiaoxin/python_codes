#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
import sys, getopt, os
import json
import re
from pattern.text.en import singularize

# 对象的名称，转为首字母大写的驼峰
def objNameOfDict(name):
    length = len(name)
    if length <= 0: return ""
    values = name.replace("-","_").split("_")
    result = []
    for value in values:
        l = len(value)
        if l <= 0: continue
        if l == 1: 
            result.append(value.upper())
        else: 
            result.append(value[0].upper())
            result.append(value[1:l])
    return "".join(result)
# 列表对应对象的名称
def objNameOfList(name):
    new_name = singularize(name)
    return objNameOfDict(new_name)
# "?\d{4}([-/]\d{1,2}){2}([T ]\d{1,2}():\d{1,2}){2}Z?)?":DateTime
# "\d{1,2}():\d{1,2}){2}":DateTime
#生成类代码
def generateClass(json_obj, name, types, template):
    items = [] # 所有字段
    sub_class_codes = [] # 子类型代码
    # 收集字段类型及子类型代码
    for key in json_obj.keys():
        value = json_obj[key]
        value_type = type(value)
        type_name = types.get(value_type.__name__,types.get("none", "UnknowType"))
        if value_type is dict:
            obj_name = objNameOfDict(key)
            sub_class_code = generateClass(value, obj_name, types, template)
            sub_class_codes.append(sub_class_code)
            items.append({"key":key,"type":type_name.replace("{{$name}}",obj_name)})
        elif value_type is list:
            obj_name = objNameOfList(key)
            if len(value) > 0 :
                sub_class_code = generateClass(value[0], obj_name, types, template)
                sub_class_codes.append(sub_class_code)
            items.append({"key":key,"type":type_name.replace("{{$name}}",obj_name)})
        else:
            items.append({"key":key,"type":type_name})
    # 替换模板文件的占位符
    def replaceCode(placeholder):
        action = placeholder.group(1) #操作
        if action == "name":
            return name
        elif action.startswith("items["):
            match_obj = re.match(r'items\[([^\]]*)\]\[([^\]]*)\]', action, re.M|re.I)
            if match_obj: 
                item_code = match_obj.group(1)
                item_sp = match_obj.group(2) #分隔代码
                item_codes = map(lambda i: item_code.replace("$key", i["key"]).replace("$type", i["type"]), items)
                return item_sp.join(item_codes)
            else:
                return placeholder.group()
        else:
            return placeholder.group()
    code = re.sub(r'\{\{\$([^\}]*)\}\}', replaceCode, template)
    sub_class_codes.insert(0, code)
    return "\n\n".join(sub_class_codes)

#用指定的模板生成代码
def generate(json_str, template, name):
    # 按空行拆分
    spindex = template.find("\n\n")
    if (spindex <= 0):
        return "模板格式不正确"
    # 类型模板
    typeTemplates = template[0:spindex]
    types = json.loads(typeTemplates)
    # 代码模板
    codeTemplate = template[spindex + 2: len(template)]
    json_obj = json.loads(json_str)
    code = generateClass(json_obj, name, types, codeTemplate)
    return code

def main(argv):
    inputfile = ''
    outputfile = ''
    outputname = ''
    templatefile = ''
    language = 'dart'
    try:
        opts, args = getopt.getopt(argv, "hi:o:l:")
    except getopt.GetoptError:
        print("接受参数为: -i JSON文件 -o 类名 -l 语言")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("接受参数为: -i JSON文件 -o 类名 -l 语言")
            sys.exit()
        elif opt == "-i":
            inputfile = arg
        elif opt == "-o":
            outputname = arg
        elif opt == "-l":
            language = arg
    my_path = os.path.abspath(os.path.dirname(__file__))
    inputfile = os.path.join(my_path, inputfile)
    outputfile = os.path.join(my_path, outputname + "." + language)
    templatefile = os.path.join(my_path, language + ".template")
    print ('输入的JSON为：', inputfile)
    print ('输出的语言为：', language)
    print ('输出的文件为：', outputfile)
    #获取Json
    file = open(inputfile, "r")
    json_str = file.read()
    file.close()
    #获取模板
    file = open(templatefile, "r")
    template = file.read()
    file.close()
    # 生成代码
    code = generate(json_str, template, outputname)
    # print(code)
    #写入代码
    file = open(outputfile, "w")
    file.write(code)
    file.close()

if __name__ == "__main__":
    main(sys.argv[1:])