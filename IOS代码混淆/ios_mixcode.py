#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

# 1.配置标识符字典, {"原名": "新名"} (手动或自动)
# 2.替换类名,若包含字典"原名",则替换该部分为"新名" class xxx (: yyy) {
# 3.替换方法名 func xxx((yyy)) ( -> yyy) {
# 4.替换变量名 [(var)(let)] xxx[: ], { (yyy,)xxx(,yyy) in, func yyy((yyy,)(yyy) xxx:yyy(,yyy)) ( -> yyy) {
# 5.替换图片名（兼容R.Swift）
# 6.修改图片元数据
# 7.修改其他资源名称

import sys, getopt, os
import re
# 随机单词
# pip3 install RandomWords
from random_words import RandomWords
import random
# # 读写properties文件
# # pip3 install sine.properties
# import sine.properties
import json
from shutil import copytree, copyfile

def collect_identifiers(path, regexs, target_set):
    """
    收集指定路径的文件中的标识符
    @path 要收集的文件路径
    @regexs 检索标识符的正则对象数组，其中标识符必须用分组包含起来且分组名为target
    @target_set 标识符集合(set),会收集不在此集合的标识符并添加进该集合
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            for regex in regexs:
                it = regex.finditer(content)
                for matched in it: 
                    target = matched.group("target")
                    if target != '' and target not in target_set:
                        target_set.add(target)
    except Exception:
        print(path,"读取文件失败")
        raise
def replace_identifiers(path, target_path, regexs, identifier_map):
    """ 
    替换指定路径的标识符
    @path 要替换的文件路径
    @target_path 替换完的文件路径
    @regexs 要替换标识符的正则对象数组，其中目标标识符必须用分组包含起来且分组名为target
    @identifier_map 标识符字典(dict),正则中检索到的标识符如果存在于该字典的key,则会替换成对应的value
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 替换找到的字符
            def replace(matched):
                target = matched.group("target")
                if target in identifier_map:
                    return identifier_map[target]
                else:
                    return target
            for regex in regexs:
                content = regex.subn(replace, content)[0]
            # 替换完写回去
            try:
                with open(target_path, 'w', encoding='utf-8') as target:
                    target.write(content)
            except Exception:
                print(target_path, "写文件失败")
                raise
    except Exception:
        print(path,"读文件失败")
        raise

class CodeMixer:
    '代码混淆器'
    # projectPath: 项目路径
    # dictionaryPath: 单词字典路径
    def __init__(self, projectPath, keywordMappingPath = None, identifierMappingPath = None):
        self.projectPath = projectPath
        project_paths = os.path.split(projectPath)
        self.target_project_path = project_paths[0] + "/" + project_paths[1] + "_mix"
        # 关键字映射
        if keywordMappingPath:
            try:
                with open(keywordMappingPath,'r') as f:
                    self.keywordMapping = json.load(f)
            except Exception:
                self.keywordMapping = {}
                print(keywordMappingPath, "加载关键字映射JSON文件失败")
                raise
        else:
            self.keywordMapping = {}
        # 标识符映射
        if identifierMappingPath:
            try:
                with open(identifierMappingPath,'r') as f:
                    self.identifierMapping = json.load(f)
            except Exception:
                self.identifierMapping = {}
                print(identifierMappingPath, "加载标识符映射JSON文件失败")
                raise
        else:
            self.identifierMapping = {}
        # 用来随机生成单词
        self.randomWords = RandomWords()
    def mappedKeyword(self, keyword):
        '获取关键字的映射，若不存在生随机生成一个,且返回的字符大小写跟关键字一致'
        mapword = None
        lkeyword = keyword.lower()
        if lkeyword in self.keywordMapping:
            mapword = self.keywordMapping[lkeyword]
        else:
            if len(lkeyword) <= 1:
                mapword = (chr(ord('a') + random.randint(0,25)))
            else:
                mapword = self.randomWords.random_word()
            self.keywordMapping[lkeyword] = mapword
        if keyword.isupper():
            if len(keyword) > 1:                                                                                                                                                                                                                                                                                                                                                                            
                return mapword.upper()
            else: 
                return mapword.title()
        elif keyword.istitle():
            return mapword.title()
        else:
            return mapword
    def buildMapping(self, identifiers):
        '构建映射'
        for identifier in identifiers:
            if identifier not in self.identifierMapping:
                keywordChars = []
                mapIdentifier = []
                for i in identifier:
                    if i in ('-','_','.','+') or i.isupper() :
                        if len(keywordChars) > 0:
                            keyword = ''.join(keywordChars)
                            mapword = self.mappedKeyword(keyword)
                            mapIdentifier.append(mapword)
                            keywordChars = []
                        if i.isupper():
                            keywordChars.append(i)
                        else:
                            mapIdentifier.append(i)
                    else:
                        keywordChars.append(i)
                if len(keywordChars) > 0:
                        keyword = ''.join(keywordChars)
                        mapword = self.mappedKeyword(keyword)
                        mapIdentifier.append(mapword)
                self.identifierMapping[identifier] = ''.join(mapIdentifier)
    def excute(self): 
        '混淆目标代码'
        # 1.查找类名
        classRegex = re.compile(r"\b(?:class|struct|enum)\s+(?P<target>[A-Za-z_][A-Za-z0-9_]*)\s*(?:<\w>)?(?:\:\w(?:,\w)*)?\s*\{")
        # 泛型名
        genericTypeRegex = re.compile(r"\b(?:class|struct|enum)\s+(?:[A-Za-z_][A-Za-z0-9_]*)\s*<\s*(?P<target>[A-Za-z_][A-Za-z0-9_]*)\s*>\s*[^\{]*\{")
        ids = set()
        # 文件名也要一起换掉
        fileNames = []
        # 递归列出当前目录下的文件并执行对应的操作
        for (root, dirs, files) in os.walk(self.projectPath):
            # Pods、R.swift不动
            if root.startswith(self.projectPath + "/Pods"):
                continue
            for file in files:
                if re.match(r'.*\.swift', file) and not file == "R.generated.swift":
                    collect_identifiers(os.path.join(root, file), [classRegex, genericTypeRegex], ids)
                    fileNames.append(os.path.splitext(file)[0])
        self.buildMapping(ids)
        self.buildMapping(fileNames)
        print("关键字映射：", self.keywordMapping)
        print("收集到的类(结构)名及映射：", self.identifierMapping)
        # 生成完导出方便备份以后同一个项目可使用同一份字典
        my_path = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(my_path, "keyword.json"),"w") as f:
            json.dump(self.keywordMapping,f)
        with open(os.path.join(my_path, "identifier.json"),"w") as f:
            json.dump(self.identifierMapping,f)
        # 开始替换关键字
        # 修改标识符
        identifierRegexs = [re.compile(r"\b(?P<target>[A-Za-z_][A-Za-z0-9_+]*)\b")]
         # 替换找到的字符
        def replace(matched):
            target = matched.group("target")
            if target in self.identifierMapping:
                return self.identifierMapping[target]
            else:
                return target
        for (root, dirs, files) in os.walk(self.projectPath):
            # 跳过Pods目录
            if root.startswith(self.projectPath + "/Pods"):
                continue
            target_root_path = identifierRegexs[0].subn(replace, root[len(self.projectPath):len(root)])[0]
            # target_root_dirs = root[len(self.projectPath):len(root)].split('/')
            # if len(target_root_dirs) > 0 :
            #     for i in range(len(target_root_dirs)):
            #         dir = target_root_dirs[i]
            #         if target_root_dirs[i] in self.identifierMapping:
            #             target_root_dirs[i] = self.identifierMapping[target_root_dirs[i]]
            target_root = self.target_project_path + target_root_path
            os.mkdir(target_root)
            for file_name in files:
                target_file = file_name
                file_name_s = os.path.splitext(file_name)
                if file_name_s[0] in self.identifierMapping:
                    target_file = self.identifierMapping[file_name_s[0]] + file_name_s[1]
                path = os.path.join(root, file_name)
                target_path = os.path.join(target_root, target_file)
                if re.match(r'.*\.(?:swift|xib|storyboard|pbxproj)', file_name) and not file_name == "R.generated.swift":
                    replace_identifiers(path, target_path, identifierRegexs, self.identifierMapping)
                else:
                    copyfile(path, target_path)
        # 单独拷贝Pods目录
        if os.path.exists(self.projectPath + "/Pods"):
            copytree(self.projectPath + "/Pods", self.target_project_path + "/Pods")

def main(argv):
    inputFile = ''
    keywordMappingFile = ''
    identifierMappingFile = ''
    clear = False
    try:
        opts, args = getopt.getopt(argv, "ht:k:i:")
    except getopt.GetoptError:
        print("接受参数为: -t 项目目录 -k 关键字映射文件 -i 标识符映射文件(json格式)")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("接受参数为: -t 项目目录 -k 关键字映射文件 -i 标识符映射文件(json格式)")
            sys.exit()
        elif opt == "-t":
            inputFile = arg
        elif opt == "-k":
            keywordMappingFile = arg
        elif opt == "-i":
            identifierMappingFile = arg
    my_path = os.path.abspath(os.path.dirname(__file__))
    inputFile = os.path.join(my_path, inputFile)
    if keywordMappingFile:
        keywordMappingFile = os.path.join(my_path, keywordMappingFile)
    if identifierMappingFile:
        identifierMappingFile = os.path.join(my_path, identifierMappingFile)
    print ('项目路径为：', inputFile)
    print ('关键字映射文件为：', keywordMappingFile)
    print ('标识符映射文件为：', identifierMappingFile)
    cm = CodeMixer(inputFile, keywordMappingFile, identifierMappingFile)
    cm.excute()

if __name__ == "__main__":
    main(sys.argv[1:])