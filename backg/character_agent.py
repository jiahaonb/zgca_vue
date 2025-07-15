"""
角色智能体 - 每个角色的独立AI智能体
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import (
    DEEPSEEK_BASE_URL, 
    DEEPSEEK_MODEL, 
    MAX_TOKENS, 
    TEMPERATURE,
    CHARACTER_SYSTEM_PROMPT_TEMPLATE
)


class CharacterAgent:
    def __init__(self, character_name: str, character_info: str, api_key: str):
        """
        初始化角色智能体
        
        Args:
            character_name: 角色名字
            character_info: 角色信息（性格、背景等）
            api_key: 分配给这个角色的API密钥
        """
        self.character_name = character_name
        self.character_info = character_info
        self.api_key = api_key
        self.conversation_history = []
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=DEEPSEEK_BASE_URL
        )
        
        # 场景和剧情信息（由调度agent设置）
        self.scene_setting = ""
        self.plot_summary = ""
        
    def set_scene_info(self, scene_setting: str, plot_summary: str):
        """
        设置场景和剧情信息
        
        Args:
            scene_setting: 场景设定
            plot_summary: 剧情大纲
        """
        self.scene_setting = scene_setting
        self.plot_summary = plot_summary
        
    def add_to_history(self, message: str):
        """
        添加对话历史
        
        Args:
            message: 对话内容
        """
        self.conversation_history.append(message)
        
    def generate_response(self, current_situation: str = "", user_character_info: str = "") -> str:
        """
        生成角色回应
        
        Args:
            current_situation: 当前情况描述
            user_character_info: 用户当前扮演的角色信息
            
        Returns:
            角色的回应
        """
        try:
            # 构建系统提示词
            system_prompt = CHARACTER_SYSTEM_PROMPT_TEMPLATE.format(
                character_name=self.character_name,
                character_info=self.character_info,
                scene_setting=self.scene_setting,
                plot_summary=self.plot_summary
            )
            
            # 如果有用户角色信息，添加到系统提示词中
            if user_character_info and user_character_info != "用户尚未选择扮演角色":
                system_prompt += f"\n\n重要提示：{user_character_info}\n请在回应时考虑用户所扮演角色的身份和特点。"
            
            # 构建用户输入
            conversation_context = "\n".join(self.conversation_history[-10:])  # 最近10条对话
            user_input = f"""
当前对话历史：
{conversation_context}

当前情况：{current_situation}

{user_character_info if user_character_info else ""}

请以{self.character_name}的身份回应：
"""
            
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False
            )
            
            character_response = response.choices[0].message.content.strip()
            
            # 将回应添加到历史记录
            self.add_to_history(character_response)
            
            return character_response
            
        except Exception as e:
            error_message = f"{self.character_name}：[角色回应生成失败: {str(e)}]"
            self.add_to_history(error_message)
            return error_message
    
    def get_character_info(self) -> Dict[str, str]:
        """
        获取角色信息
        
        Returns:
            角色信息字典
        """
        return {
            "name": self.character_name,
            "info": self.character_info,
            "api_key": self.api_key[:20] + "..."  # 只显示前20个字符
        }
    
    def clear_history(self):
        """
        清空对话历史
        """
        self.conversation_history.clear() 