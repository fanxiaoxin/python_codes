#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

from ast import walk
import sys, getopt, os
import re
from typing import Any, AnyStr, Mapping, Pattern, Union, Optional, Tuple
# 随机单词
# pip3 install RandomWords
from random_words import RandomWords
# 元数据字段文档：https://www.exiv2.org/metadata.html
# https://github.com/LeoHsiao1/pyexiv2
import pyexiv2
import random
# # 读写properties文件
# # pip3 install sine.properties
# import sine.properties
import json
from shutil import copytree, copyfile, ignore_patterns
# from abc import ABC, ABCMeta, abstractmethod

class IdeneitiferPattern:
    """
    标识符正则匹配模式
    """
    def __init__(self, regex: AnyStr, group: Union[str, int, list] = None, flags: Union[int, re.RegexFlag] = 0):
        # 正则表达式
        self.regex = re.compile(regex, flags=flags)
        # 正则中要取的标识符的分组，若为多个则依次判断取第一个有值的值，若为空则取整个字符串
        if group == None:
            self.groups = [0]
        if isinstance(group, list):
            self.groups = group
        else:
            self.groups = [group]

    def group(self, matched: re.Match) -> Optional[Tuple[str, str]]:
        """
        返回匹配的group
        0 匹配的字符串
        1 匹配的group名称
        """
        value = matched.group(self.groups[0])
        idx = 1
        while value == None and idx < len(self.groups):
            value = matched.group(self.groups[idx])
            idx += 1
        if value == '':
            return None
        return value

class IdentifierMappingManager:
    """
    标识符映射管理：负责维护关键字映射及标识符映射
    """
    # 用来随机生成单词
    __randomWords = RandomWords()
    
    def __init__(self, keyword_mapping: dict = None, identifier_mapping: dict = None):
        """
        @keyword_mapping dict: 初始化关键字映射 
        @identifier_mapping dict: 初始化标识符映射 
        """
        if keyword_mapping:
            self.keyword_mapping = keyword_mapping
        else:
            self.keyword_mapping = {}
        if identifier_mapping:
            self.identifier_mapping = identifier_mapping
        else:
            self.identifier_mapping = {}
    def get_mapping_keyword(self, keyword: str) -> str:
        """
        获取映射的关键字，若不存在成生成
        """
        if keyword in self.keyword_mapping:
            return self.keyword_mapping[keyword]
        else:
            mapping = IdentifierMappingManager.__randomWords.random_word()
            self.keyword_mapping[keyword] = mapping
            return mapping
    def get_mapping_identifier(self, identifier: str) -> str:
        """
        获取映射的标识符，若不存在则生成
        """
        if identifier in self.identifier_mapping:
            return self.identifier_mapping[identifier]
        else:
            def replace_keyword_for_regex(matched: re.Match):
                """
                替换关键字为映射的关键字，若不存在则生成，用于正则的替换函数
                """
                target = matched.group("target1")
                if target == None:
                    target = matched.group("target2")
                return self.get_mapping_keyword(target)
            #拆分单词关键字并替换为对应的关键字映射
            mapping = re.subn(r'(?:\b|[^A-Za-z])(?P<target1>[a-z]+)|(?P<target2>[A-Z][a-z]*)', replace_keyword_for_regex, identifier)[0]
            self.identifier_mapping[identifier] = mapping
            return mapping

    def collect(self, content: str, pattern: IdeneitiferPattern):
        """
        从指定字符串中收集指定正则的标识符
        @content 要收集标识符的字符串
        @regex 要收集的标识符正则类
        @group_index 正则中指定的标识符分组名称或索引，若不指定则使用整个匹配的字符
        """
        it = pattern.regex.finditer(content)
        for matched in it:
            identifier = pattern.group(matched)
            if identifier != None:
                self.get_mapping_identifier(identifier)
    
    def replace(self, content: str, pattern: IdeneitiferPattern) -> str :
        """
        将指定的字符串中存在于标识符字典的字符串替换为对应的映射字符串
        @content 要替换标识符的字符串
        @regex 要替换的标识符判断正则类
        @group_index 正则中指定的标识符分组名称或索引，若不指定则使用整个匹配的字符
        """
        def replace_identifier_for_regex(matched: re.Match):
            """
            替换标识符为映射的标识符，用于正则的替换函数
            """
            group = pattern.group(matched)
            target = group[0]
            if target in self.identifier_mapping:
                target = self.identifier_mapping[target]
                target_pos = matched.span(group[1])
                all = matched.group(0)
                pos = matched.span(0)
                return all[0:target_pos[0] - pos[0]] + target + all[target_pos[1] - pos[0]:pos[1] - pos[0]]
            else: 
                return matched.group(0)
        #获取标识符并替换为对应的标识符映射
        return pattern.regex.subn(replace_identifier_for_regex, content)[0]

class FilePattern:
    """
    文件匹配模式
    """
    def __init__(self, file_path_pattern: AnyStr, identifier_patterns: list):
        """
        @file_name_pattern 文件路径及名称匹配，匹配该文件路径和名称的才会执行标识符的收集或替换
        @identifier_pattern 标识符匹配
        """
        self.file_path_pattern = re.compile(file_path_pattern)
        self.identifier_patterns = identifier_patterns

    def is_file_matched(self, file_path) -> bool:
        """
        是否匹配该文件路径
        """
        return self.file_path_pattern.match(file_path) != None

class FileMixConfig:
    """
    文件混淆配置
    """
    def __init__(self):
        # 路径收集标识符模式
        self.collect_path_patterns: list[FilePattern] = None
        # 文件内容收集标识符模式
        self.collect_content_patterns: list[FilePattern] = None
        # 路径混淆标识符模式
        self.replace_path_patterns: list[FilePattern] = None
        # 文件内容混淆标识符模式
        self.replace_content_patterns: list[FilePattern] = None

class FileMixManager:
    """
    文件混淆管理类：负责管理要混淆的文件及混淆的方式和操作
    """
    def __init__(self, root_path: str, identifier_mapping: IdentifierMappingManager, config: FileMixConfig, ignore_path_regexs: Union[list, AnyStr] = None):
        """
        @root_path 项目根目录
        @identifier_mapping 标识符映射管理器
        @config 文件混淆配置
        @ignore_path_regexs 要忽略的路径正则
        """
        self.root_path = root_path
        self.identifier_mapping = identifier_mapping
        self.config = config
        if ignore_path_regexs == None:
            self.ignore_path_patterns = None
        if isinstance(ignore_path_regexs, list):
            self.ignore_path_patterns = map(lambda regex: re.compile(regex), ignore_path_regexs)
        else:
            self.ignore_path_patterns = [re.compile(ignore_path_regexs)]

    def collect_identifiers_for_path(self, path: str):
        """
        收集路径上的标识符
        """
        if self.config.collect_path_patterns:
            for pattern in self.config.collect_path_patterns:
                if pattern.is_file_matched(path):
                    for ip in pattern.identifier_patterns:
                        self.identifier_mapping.collect(path, ip)
    def replace_path(self, path: str) -> str:
        """
        混淆指定路径，返回新的路径
        """
        result = path
        if self.config.replace_path_patterns:
            for pattern in self.config.replace_path_patterns:
                if pattern.is_file_matched(path):
                    for ip in pattern.identifier_patterns:
                        result = self.identifier_mapping.replace(result, ip)
        return result
    
    def collect_identifiers_for_file_content(self, path: str):
        """
        收集指定文件要映射的标识符
        """
        if self.config.collect_content_patterns:
            content: str = None
            for pattern in self.config.collect_content_patterns:
                if pattern.is_file_matched(path):
                    for ip in pattern.identifier_patterns:
                        if content == None:
                            try:
                                with open(path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                            except Exception:
                                print(path,"读取文件失败")
                                raise
                        self.identifier_mapping.collect(content, ip)
            
    def replace_file_content(self, path: str) -> str:
        """
        混淆指定文件的内容，并返回新的内容
        """
        content: str = None
        if self.config.replace_content_patterns:
            for pattern in self.config.replace_content_patterns:
                if pattern.is_file_matched(path):
                    for ip in pattern.identifier_patterns:
                        if content == None:
                            try:
                                with open(path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                            except Exception:
                                print(path,"读取文件失败")
                                raise
                        content = self.identifier_mapping.replace(content, ip)
        return content
    def is_ignore(self, path: str) -> bool:
        """
        判断指定路径是否要忽略
        """
        if self.ignore_path_patterns:
            for pattern in self.ignore_path_patterns:
                if pattern.match(path):
                    return True
        return False
    def collect_identifiers(self):
        """
        收集标识符
        """
        # 递归列出当前目录下的文件并执行对应的操作
        for (root, dirs, files) in os.walk(self.root_path):
            path = root[len(self.root_path):len(root)]
            if not self.is_ignore(path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    path = file_path[len(self.root_path):len(file_path)]
                    if not self.is_ignore(path):
                        self.collect_identifiers_for_path(path)
                        self.collect_identifiers_for_file_content(file_path)
    def mix_file(self, file_path, new_file_path):
        """
        混淆指定文件
        @path 指定文件路径
        @target_path 混淆后的路径
        """
        new_file_content = self.replace_file_content(file_path)
        if new_file_content:
            # 替换后的内容写到文件
            try:
                with open(new_file_path, 'w+', encoding='utf-8') as target:
                    target.write(new_file_content)
            except Exception:
                print(new_file_path, "写文件失败")
                raise
            # 若新的路径不一样则删掉原文件
            if new_file_path != file_path:
                os.remove(file_path)
    def mix(self):
        """
        混淆根目录下所有匹配的内容
        """
        # 递归列出当前目录下的文件并执行对应的操作
        # 因为混淆可能会改变路径，防止二次混淆，先把遍历目录保存下来
        walk_data: list[Tuple[str, list[str]]] = []
        for (root, dirs, files) in os.walk(self.root_path):
            walk_data.append([root, files])
        # 使用遍历好的路径来混淆
        for (root, files) in walk_data:
            path = root[len(self.root_path):len(root)]
            if not self.is_ignore(path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    path = file_path[len(self.root_path):len(file_path)]
                    if not self.is_ignore(path):
                        new_file_path = os.path.join(self.root_path, self.replace_path(path))
                        self.mix_file(file_path, new_file_path)
                            

class ClassNameMixManager(FileMixManager):
    """
    类名混淆管理：负责管理类名的混淆方案
    """
    def __init__(self, root_path: str, identifier_mapping: IdentifierMappingManager, ignore_path_regexs: Union[list, AnyStr] = None):
        """
        @root_path 项目根目录
        @identifier_mapping 标识符映射管理器
        @ignore_path_regexs 要忽略的路径正则
        """
        config = FileMixConfig()
        config.collect_path_patterns = [FilePattern(r".*\.swift$", [IdeneitiferPattern(r".*")])]
        config.collect_content_patterns = [FilePattern(r".*\.swift$", [IdeneitiferPattern(r"\b(?:class|struct|enum)\s+(?P<target>[A-Za-z_][A-Za-z0-9_]*)\s*(?:<\w>)?(?:\:\w(?:,\w)*)?\s*\{", "target")])]
        config.replace_path_patterns = [FilePattern(r".*\.swift$", [IdeneitiferPattern(r"(?P<target>[^/]*)\.swift", "target")])]
        config.replace_content_patterns = [FilePattern(r'.*\.(?:swift|xib|storyboard|pbxproj)$', [IdeneitiferPattern(r"\b[A-Za-z_][A-Za-z0-9_+]*\b")])]
        super().__init__(root_path, identifier_mapping, config, ignore_path_regexs)
    
class ImageMixManager(FileMixManager):
    """
    图片混淆管理：负责管理图片的混淆方案
    """
    def __init__(self, root_path: str, identifier_mapping: IdentifierMappingManager, image_xmp: dict, ignore_path_regexs: Union[list, AnyStr] = None):
        """
        @root_path 项目根目录
        @identifier_mapping 标识符映射管理器
        @image_xmp 图片修改后的Xmp元数据,如: {"Xmp.dc.description":"描述", "Xmp.dc.creator":"作者"}
        @ignore_path_regexs 要忽略的路径正则
        """
        config = FileMixConfig()
        config.collect_path_patterns = [FilePattern(r".*\.xcassets(?:/.*)/.*\.imageset/Contents.json$", [IdeneitiferPattern(r".*\.xcassets(?:/.*)/(?P<target>.*)\.imageset", "target")])]
        config.collect_content_patterns = None
        config.replace_path_patterns = [FilePattern(r".*\.xcassets(?:/.*)/.*\.imageset/.*$", [IdeneitiferPattern(r".*\.xcassets(?:/.*)/(?P<target>.*)\.imageset", "target")])]
        config.replace_content_patterns = None
        super().__init__(root_path, identifier_mapping, config, ignore_path_regexs)
        self.image_xmp = image_xmp

    def mix_file(self, file_path, new_file_path):
        """
        混淆指定文件，图片特殊处理，修改元数据并改名
        @path 指定文件路径
        @target_path 混淆后的路径
        """
        # 先写元数据
        if re.match(".*\.(?:png|jpg)$"):
            try:
                with open(file_path, 'rb+') as f:
                    with pyexiv2.ImageData(f.read()) as img:
                        img.clear_exif()
                        img.clear_iptc()
                        img.clear_xmp()
                        img.modify_xmp(self.image_xmp)
                        f.seek(0)
                        # 获取图片的字节数据并保存到文件中
                        f.write(img.get_bytes())
            except Exception:
                print(file_path,"重置元数据失败")
        # 新旧路径不一样则移动位置
        if file_path != new_file_path:
            os.rename(file_path, new_file_path)
            # 移除空目录
            old_dir = os.path.dirname(file_path)
            if not os.listdir(old_dir):
                os.rmdir(old_dir)

class IosProjectMixer:
    'IOS项目混淆器'
    # projectPath: 项目路径
    # dictionaryPath: 单词字典路径
    def __init__(self, project_path: str, keyword_mapping_path: str = None, identifier_mapping_path: str = None):
        self.project_path = project_path.rstrip('/')
        self.target_project_path = self.project_path + "_mix"
        # 关键字映射
        keyword_mapping = {}
        if not keyword_mapping_path: # 不存在则使用默认路径
            keyword_mapping_path = self.project_path + "/mix_keyword.json"
        if keyword_mapping_path and os.path.exists(keyword_mapping_path) and os.path.isfile(keyword_mapping_path) :
            try:
                with open(keyword_mapping_path,'r') as f:
                    keyword_mapping = json.load(f)
            except Exception:
                print(keyword_mapping_path, "加载关键字映射JSON文件失败")
                raise
        # 标识符映射
        identifier_mapping: dict = None
        if not identifier_mapping_path: # 不存在则使用默认路径
            identifier_mapping_path = self.project_path + "/mix_identifier.json"
        if identifier_mapping_path and os.path.exists(identifier_mapping_path) and os.path.isfile(keyword_mapping_path):
            try:
                with open(identifier_mapping_path,'r') as f:
                    identifier_mapping = json.load(f)
            except Exception:
                print(identifier_mapping_path, "加载标识符映射JSON文件失败")
                raise
        self.identifier_mapping = IdentifierMappingManager(keyword_mapping, identifier_mapping)

    def mix(self):
        """
        混淆目标项目
        """
        ignore_path = r'^(?:Pods)'
        classMix = ClassNameMixManager(self.project_path, self.identifier_mapping, ignore_path)
        imageMix = ImageMixManager(self.project_path, self.identifier_mapping, {"":""}, ignore_path)
        # 1.收集标识符
        classMix.collect_identifiers()
        imageMix.collect_identifiers()
        print("关键字：\n", self.identifier_mapping.keyword_mapping)
        print("标识符：\n", self.identifier_mapping.identifier_mapping)
        # 2.拷贝项目到新的位置来修改
        copytree(self.project_path, self.target_project_path)
        classMix.root_path = self.target_project_path
        imageMix.root_path = self.target_project_path
        # 3.混淆
        classMix.mix()
        imageMix.mix()
        # 4.保存混淆的字典用于下次做同样的混淆
        try:
            if self.identifier_mapping.keyword_mapping:
                with open(self.project_path + "/mix_keyword.json",'w+', encoding='utf-8') as f:
                    json.dump(self.identifier_mapping.keyword_mapping,f)
            if self.identifier_mapping.identifier_mapping:
                with open(self.project_path + "mix_identifier.json",'w+', encoding='utf-8') as f:
                    json.dump(self.identifier_mapping.identifier_mapping,f)
        except Exception:
            print("保存字典文件失败", self.project_path + "/mix_keyword.json")
            raise

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
    ipm = IosProjectMixer(inputFile, keywordMappingFile, identifierMappingFile)
    ipm.mix()

if __name__ == "__main__":
    main(sys.argv[1:])