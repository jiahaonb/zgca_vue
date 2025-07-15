"""
调度智能体 - 负责剧本创建、角色管理和对话调度
"""

import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from character_agent import CharacterAgent
from api_pool import APIKeyPool
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
from dashscope import ImageSynthesis
import os
from config import (
    DEEPSEEK_BASE_URL, 
    DEEPSEEK_MODEL, 
    MAX_TOKENS, 
    TEMPERATURE,
    SCHEDULER_SYSTEM_PROMPT,
    USER_CHARACTER_NAME
)


class SchedulerAgent:
    def __init__(self, api_key: str):
        """
        初始化调度智能体
        
        Args:
            api_key: 调度agent的API密钥
        """
        self.api_key = api_key
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=DEEPSEEK_BASE_URL
        )
        
        self.api_pool = APIKeyPool()
        self.characters: Dict[str, CharacterAgent] = {}
        self.scene_setting = ""
        self.plot_summary = ""
        self.conversation_history = []
        
        # 用户当前扮演的角色信息
        self.user_current_character = None  # 用户当前扮演的角色名
        self.user_character_info = None     # 用户扮演角色的详细信息
    
    def create_script_setting(self, user_input: str) -> Dict[str, Any]:
        """
        根据用户输入创建剧本设定
        
        Args:
            user_input: 用户输入的场景和限制
            
        Returns:
            剧本设定信息
        """
        try:
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": SCHEDULER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False
            )
            
            script_setting = response.choices[0].message.content.strip()
            
            # 解析剧本设定
            parsed_setting = self._parse_script_setting(script_setting)
            
            # 保存场景和剧情信息
            self.scene_setting = parsed_setting.get("scene_setting", "")
            self.plot_summary = parsed_setting.get("plot_summary", "")
            
            return parsed_setting
            
        except Exception as e:
            return {"error": f"剧本设定创建失败: {str(e)}"}
    
    def _parse_script_setting(self, script_setting: str) -> Dict[str, Any]:
        """
        解析剧本设定文本
        
        Args:
            script_setting: 剧本设定文本
            
        Returns:
            解析后的设定信息
        """
        result = {
            "full_setting": script_setting,
            "scene_setting": "",
            "characters": [],
            "plot_summary": ""
        }
        
        # 提取场景设定
        scene_match = re.search(r'【场景设定】\s*\n(.*?)(?=【|$)', script_setting, re.DOTALL)
        if scene_match:
            result["scene_setting"] = scene_match.group(1).strip()
        
        # 提取主要角色
        characters_match = re.search(r'【主要角色】\s*\n(.*?)(?=【|$)', script_setting, re.DOTALL)
        if characters_match:
            characters_text = characters_match.group(1).strip()
            # 解析角色信息（格式：角色名|性格特点|背景）
            character_lines = [line.strip() for line in characters_text.split('\n') if line.strip()]
            for line in character_lines:
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        character_name = parts[0].strip()
                        character_info = '|'.join(parts[1:]).strip()
                        result["characters"].append({
                            "name": character_name,
                            "info": character_info
                        })
        
        # 提取剧情大纲
        plot_match = re.search(r'【剧情大纲】\s*\n(.*?)(?=【|$)', script_setting, re.DOTALL)
        if plot_match:
            result["plot_summary"] = plot_match.group(1).strip()
        
        return result
    
    def create_characters(self, characters_info: List[Dict[str, str]]) -> bool:
        """
        创建角色智能体
        
        Args:
            characters_info: 角色信息列表
            
        Returns:
            是否创建成功
        """
        try:
            if len(characters_info) == 0:
                return False
            
            # 分离用户主角和AI角色
            user_character = None
            ai_characters = []
            
            for character_info in characters_info:
                if USER_CHARACTER_NAME in character_info["name"]:
                    user_character = character_info
                else:
                    ai_characters.append(character_info)
            
            # 确保有用户主角
            if not user_character:
                print("❌ 未找到用户主角信息")
                return False
            
            # 记录用户主角信息（不需要创建AI智能体）
            self.characters[USER_CHARACTER_NAME] = "user_character"
            
            # 只为AI角色分配API密钥
            ai_character_count = len(ai_characters)
            if ai_character_count > 0:
                api_keys = self.api_pool.get_keys(ai_character_count)
                
                # 创建AI角色智能体
                for i, character_info in enumerate(ai_characters):
                    character_name = character_info["name"]
                    character_detail = character_info["info"]
                    api_key = api_keys[i]
                    
                    character_agent = CharacterAgent(character_name, character_detail, api_key)
                    character_agent.set_scene_info(self.scene_setting, self.plot_summary)
                    
                    self.characters[character_name] = character_agent
            
            print(f"✅ 创建完成：用户主角 + {ai_character_count} 个AI角色")
            return True
            
        except Exception as e:
            print(f"❌ 角色创建失败: {str(e)}")
            return False
    
    def decide_next_speaker(self, current_situation: str = "") -> Optional[str]:
        """
        决定下一个说话的角色（包括用户主角）
        
        Args:
            current_situation: 当前情况描述
            
        Returns:
            下一个说话的角色名字
        """
        try:
            # 构建对话历史
            conversation_context = "\n".join(self.conversation_history[-10:])  # 最近10条对话
            
            # 构建可选角色列表
            character_list = ", ".join(self.characters.keys())
            
            user_input = f"""
当前场景：{self.scene_setting}

可选角色：{character_list}

最近对话历史：
{conversation_context}

当前情况：{current_situation}

请决定下一个应该说话的角色。
"""
            
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": SCHEDULER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=TEMPERATURE,
                max_tokens=512,
                stream=False
            )
            
            decision_text = response.choices[0].message.content.strip()
            
            # 从回应中提取角色名
            next_speaker = self._extract_character_name(decision_text)
            
            return next_speaker
            
        except Exception as e:
            print(f"❌ 角色调度失败: {str(e)}")
            return None
    
    def decide_next_ai_speaker(self, current_situation: str = "") -> Optional[str]:
        """
        决定下一个说话的AI角色（不包括用户主角）
        
        Args:
            current_situation: 当前情况描述
            
        Returns:
            下一个说话的AI角色名字
        """
        try:
            # 构建对话历史
            conversation_context = "\n".join(self.conversation_history[-10:])  # 最近10条对话
            
            # 构建AI角色列表（排除用户主角）
            ai_characters = [name for name in self.characters.keys() if name != USER_CHARACTER_NAME]
            if not ai_characters:
                print("❌ 没有可用的AI角色")
                return None
            
            character_list = ", ".join(ai_characters)
            
            user_input = f"""
当前场景：{self.scene_setting}

可选AI角色：{character_list}

最近对话历史：
{conversation_context}

当前情况：{current_situation}

请从AI角色中决定下一个应该说话的角色。注意：不要选择用户主角"{USER_CHARACTER_NAME}"。
"""
            
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": SCHEDULER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=TEMPERATURE,
                max_tokens=512,
                stream=False
            )
            
            decision_text = response.choices[0].message.content.strip()
            
            # 从回应中提取角色名
            next_speaker = self._extract_character_name(decision_text, ai_only=True)
            
            return next_speaker
            
        except Exception as e:
            print(f"❌ AI角色调度失败: {str(e)}")
            return None
    
    def _extract_character_name(self, decision_text: str, ai_only: bool = False) -> Optional[str]:
        """
        从调度决定中提取角色名
        
        Args:
            decision_text: 调度决定文本
            ai_only: 是否只从AI角色中选择
            
        Returns:
            角色名字
        """
        # 获取候选角色列表
        if ai_only:
            candidate_characters = [name for name in self.characters.keys() if name != USER_CHARACTER_NAME]
        else:
            candidate_characters = list(self.characters.keys())
        
        if not candidate_characters:
            return None
        
        # 尝试匹配 "下一个说话的角色：角色名" 格式
        match = re.search(r'下一个说话的角色：(.+)', decision_text)
        if match:
            character_name = match.group(1).strip()
            # 检查是否是有效的角色名
            for name in candidate_characters:
                if name in character_name:
                    return name
        
        # 如果没有匹配到格式，尝试直接在文本中查找角色名
        for character_name in candidate_characters:
            if character_name in decision_text:
                return character_name
        
        # 如果都没找到，返回第一个候选角色
        if candidate_characters:
            return candidate_characters[0]
        
        return None
    
    def add_to_history(self, message: str):
        """
        添加到对话历史
        
        Args:
            message: 对话内容
        """
        self.conversation_history.append(message)
        
        # 同时添加到所有AI角色的历史记录
        for name, character in self.characters.items():
            if name != USER_CHARACTER_NAME:  # 跳过用户主角
                character.add_to_history(message)
    
    def get_character_agent(self, character_name: str) -> Optional[CharacterAgent]:
        """
        获取指定角色的智能体
        
        Args:
            character_name: 角色名字
            
        Returns:
            角色智能体，如果是用户主角则返回None
        """
        if character_name == USER_CHARACTER_NAME:
            return None  # 用户主角不是AI智能体
        return self.characters.get(character_name)
    
    def get_characters_info(self) -> List[Dict[str, str]]:
        """
        获取所有角色信息
        
        Returns:
            角色信息列表
        """
        characters_info = []
        for name, character in self.characters.items():
            if name == USER_CHARACTER_NAME:
                # 用户主角的信息
                characters_info.append({
                    "name": USER_CHARACTER_NAME,
                    "info": "用户扮演的主角",
                    "type": "user"
                })
            else:
                # AI角色的信息
                character_info = character.get_character_info()
                character_info["type"] = "ai"
                characters_info.append(character_info)
        return characters_info
    
    def clear_all_history(self):
        """
        清空所有历史记录
        """
        self.conversation_history.clear()
        for name, character in self.characters.items():
            if name != USER_CHARACTER_NAME:  # 跳过用户主角
                character.clear_history()

    def generate_user_dialogue(self, max_tokens: int = 150) -> List[str]:
        """
        根据历史上下文生成基于历史人物角色的对话建议

        Args:
            max_tokens: 生成内容的最大长度

        Returns:
            包含历史人物角色信息的对话建议列表，格式："[角色名] 台词内容"
        """
        try:
            # 获取可用的历史人物角色（排除用户角色"我"）
            available_characters = []
            for char_name, char_agent in self.characters.items():
                if char_name != USER_CHARACTER_NAME:
                    available_characters.append({
                        'name': char_name,
                        'info': char_agent.character_info
                    })

            # 如果没有可用角色，返回默认选项
            if not available_characters:
                return ["[用户] 我认为我们应该推进这个方案", "[用户] 这个方案是不是风险太大了？"]

            # 选择2个不同的历史人物角色
            import random
            selected_characters = random.sample(available_characters, min(2, len(available_characters)))
            
            # 构建对话上下文
            context = "\n".join([
                f"场景设定: {self.scene_setting}",
                f"剧情大纲: {self.plot_summary}",
                "最近对话历史:",
                *[f"- {line}" for line in self.conversation_history[-6:]]
            ])

            dialogues = []
            
            for character in selected_characters:
                # 为每个角色生成台词
                prompt = f"""
你是一个专业的剧本创作助手，现在需要为历史人物{character['name']}生成台词。

角色信息：{character['info']}

当前上下文：
{context}

请以{character['name']}的身份和性格特点，生成一句符合当前情境的台词。
要求：
1. 台词长度不超过20个字
2. 体现{character['name']}的性格特征
3. 符合当前剧情发展
4. 只返回台词内容，不要添加其他说明

台词：
"""
                
                response = self.client.chat.completions.create(
                    model=DEEPSEEK_MODEL,
                    messages=[
                        {"role": "system", "content": f"你擅长模拟历史人物{character['name']}的语言风格和性格特点"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=max_tokens,
                    stream=False
                )

                dialogue = response.choices[0].message.content.strip()
                # 去掉可能的引号和多余字符
                dialogue = dialogue.strip('"\'').strip()
                
                # 格式化为 "[角色名] 台词内容"
                formatted_dialogue = f"[{character['name']}] {dialogue}"
                dialogues.append(formatted_dialogue)

            return dialogues if len(dialogues) >= 2 else dialogues + ["[用户] 我们继续推进剧情吧"]

        except Exception as e:
            print(f"❌ 台词生成失败: {str(e)}")
            return ["[用户] 我觉得这个主意不错", "[用户] 我们是否需要再考虑一下？"]

    def text_to_image(self,prompt,save_dir='./output'):
        print('----sync call, please wait a moment----')
        rsp = ImageSynthesis.call(
            api_key="sk-bba8d81c77b14d59b41e585570d86e7c",
            model="wanx2.0-t2i-turbo",
            prompt=prompt,
            n=1,
            size='1024*1024'
        )
        print('response: %s' % rsp)
        if rsp.status_code == HTTPStatus.OK:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            for result in rsp.output.results:
                save_path = os.path.join(save_dir, "first.png")
                # 使用with语句确保文件自动关闭
                with open(save_path, 'wb+') as f:
                    f.write(requests.get(result.url).content)
                    f.flush()  # 强制将缓冲区内容写入磁盘
                    os.fsync(f.fileno())  # 确保文件内容已写入磁盘
                print(f"图片已保存到: {save_path}")
            return save_path
        else:
            print('sync_call Failed, status_code: %s, code: %s, message: %s' %
                  (rsp.status_code, rsp.code, rsp.message))
            return None

    def generate_graph(self, num: int) -> Optional[str]:
        """
        根据最新对话和场景生成图片描述并保存图片

        Args:
            num: 图片编号，用于创建子目录

        Returns:
            图片保存路径，失败时返回None
        """
        try:
            # 1. 构建图片描述文本（使用显式换行符\n）
            scene_desc = self.scene_setting
            plot_desc = self.plot_summary
            recent_dialogue = '\n'.join(self.conversation_history[-3:])
            scene_key = self.scene_setting.split('。')[0]
            characters = ', '.join(self.characters.keys())

            image_description = (
                    "当前场景描述：\n" + scene_desc + "\n\n" +
                    "剧情发展：\n" + plot_desc + "\n\n" +
                    "最近对话内容：\n" + recent_dialogue + "\n\n" +
                    "基于以上内容，生成的画面应包含以下元素：\n" +
                    "1. 场景：" + scene_key + "（重点表现环境氛围）\n" +
                    "2. 角色：" + characters + "（体现角色特征）\n" +
                    "3. 动作：根据最近对话表现角色互动\n" +
                    "4. 情绪：符合当前剧情发展状态"
            )

            print("📝 生成的图片描述：")
            print(image_description)

            # 2. 获取保存路径
            save_dir = './output'
            sub_dir = f"{save_dir}/{num}"
            os.makedirs(sub_dir, exist_ok=True)

            # 3. 转换为适合模型的prompt
            model_prompt = (
                    "专业摄影风格，8K高清，" + scene_key + "，" +
                    "包含角色：" + characters + "，" +
                    "表现场景氛围和角色互动"
            )

            # 4. 生成并保存图片
            print("🖼️ 正在生成图片...")
            image_path = self.text_to_image(model_prompt, sub_dir)

            if image_path:
                print(f"✅ 图片已保存到: {image_path}")
                return image_path
            return None

        except Exception as e:
            print(f"❌ 图片生成出错: {str(e)}")
            return None
    
    def set_user_character(self, character_name: str) -> bool:
        """
        设置用户当前扮演的角色
        
        Args:
            character_name: 角色名
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if character_name in self.characters:
                self.user_current_character = character_name
                self.user_character_info = self.characters[character_name].character_info
                print(f"✅ 用户角色已设置为: {character_name}")
                return True
            else:
                print(f"❌ 角色 {character_name} 不存在")
                return False
        except Exception as e:
            print(f"❌ 设置用户角色失败: {str(e)}")
            return False
    
    def get_user_character(self) -> tuple:
        """
        获取用户当前扮演的角色信息
        
        Returns:
            tuple: (角色名, 角色信息)
        """
        return self.user_current_character, self.user_character_info
    
    def clear_user_character(self):
        """
        清除用户角色设置
        """
        self.user_current_character = None
        self.user_character_info = None
        print("✅ 用户角色设置已清除")
    
    def get_user_character_context(self) -> str:
        """
        获取用户角色的上下文信息，用于传递给大模型
        
        Returns:
            str: 用户角色上下文信息
        """
        if self.user_current_character and self.user_character_info:
            return f"用户当前扮演角色：{self.user_current_character}\n角色信息：{self.user_character_info}"
        else:
            return "用户尚未选择扮演角色"