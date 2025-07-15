"""
剧本系统核心逻辑 - 整合调度agent和角色agents的交互流程
"""

from typing import Optional, Dict, Any
from scheduler_agent import SchedulerAgent
from api_pool import APIKeyPool
from config import API_KEYS, USER_CHARACTER_NAME
from record_voc import record_and_recognize
import threading

class ScriptSystem:
    def __init__(self):
        """
        初始化剧本系统
        """
        # 确保有可用的API密钥
        if not API_KEYS:
            raise ValueError("请在config.py中设置API_KEYS")
        
        # 使用第一个API密钥作为调度agent的密钥
        scheduler_api_key = API_KEYS[0]
        self.scheduler = SchedulerAgent(scheduler_api_key)
        
        self.is_initialized = False
        self.conversation_count = 0
        self.last_speaker = None  # 记录上一个说话的角色
        
        # 图片生成相关
        self.image_generation_interval = 3  # 每3轮对话生成一次图片
        self.last_image_round = 0  # 上次生成图片的轮次
        
    def initialize_script(self, user_input: str) -> Dict[str, Any]:
        """
        初始化剧本设定和角色
        
        Args:
            user_input: 用户输入的场景和限制
            
        Returns:
            初始化结果
        """
        print("🎭 正在创建剧本设定...")
        
        # 创建剧本设定
        script_setting = self.scheduler.create_script_setting(user_input)
        
        if "error" in script_setting:
            return script_setting
        
        print("📝 剧本设定创建完成！")
        print("-" * 50)
        print(script_setting["full_setting"])
        print("-" * 50)
        
        # 创建角色智能体
        characters_info = script_setting.get("characters", [])
        if not characters_info:
            return {"error": "未能从剧本设定中提取到角色信息"}
        
        print(f"🤖 正在创建 {len(characters_info)} 个角色智能体...")
        
        success = self.scheduler.create_characters(characters_info)
        if not success:
            return {"error": "角色智能体创建失败"}
        
        self.is_initialized = True
        
        print("✅ 角色智能体创建完成！")
        print("\n🎯 创建的角色：")
        for character_info in self.scheduler.get_characters_info():
            print(f"  - {character_info['name']}: {character_info['info']}")
        
        # 启动后台任务生成初始场景图片（不等待完成）
        print("\n🖼️ 正在后台生成初始场景图片...")
        threading.Thread(
            target=self._generate_initial_image_async, 
            daemon=True
        ).start()
        
        return {
            "success": True,
            "characters_count": len(characters_info),
            "characters": characters_info
        }
    
    def _generate_initial_image_async(self):
        """
        异步生成初始场景图片的后台任务
        """
        try:
            initial_image_path = self.scheduler.generate_graph(0)  # 使用0作为初始图片编号
            if initial_image_path:
                print(f"✅ 初始场景图片生成完成: {initial_image_path}")
            else:
                print("⚠️ 初始场景图片生成失败，但不影响剧本功能")
        except Exception as e:
            print(f"❌ 后台生成初始图片时出错: {str(e)}")
    
    def check_and_trigger_background_image_generation(self, current_round: int) -> None:
        """
        检查是否需要触发后台图片生成
        
        Args:
            current_round: 当前对话轮次
        """
        if not self.is_initialized:
            return
            
        # 检查是否达到图片生成间隔
        rounds_since_last_image = current_round - self.last_image_round
        
        if rounds_since_last_image >= self.image_generation_interval:
            print(f"🎨 第{current_round}轮：触发后台图片生成 (上次生成：第{self.last_image_round}轮)")
            self.scheduler.generate_background_image(current_round)
            self.last_image_round = current_round
        else:
            remaining_rounds = self.image_generation_interval - rounds_since_last_image
            print(f"📊 第{current_round}轮：距离下次图片生成还有 {remaining_rounds} 轮")

    def start_conversation(self, rounds: int = 10) -> None:
        """
        开始多轮对话
        
        Args:
            rounds: 对话轮数
        """
        if not self.is_initialized:
            print("❌ 请先初始化剧本设定")
            return
        
        print(f"\n🎬 开始 {rounds} 轮对话...")
        print("💡 优化的交互体验：")
        print("  - 当需要您说话时，直接输入台词，按回车跳过")
        print("  - 您说话后会直接调度AI角色，AI说话后才会再次询问您")
        print("=" * 60)
        
        # 重置对话状态
        self.last_speaker = None
        
        for round_num in range(1, rounds + 1):
            print(f"\n【第 {round_num} 轮对话】")
            print("-" * 30)
            
            # 根据上一个说话的人决定流程
            if self.last_speaker != USER_CHARACTER_NAME:
                # 上一个不是用户说话（或者是第一轮），询问用户

                choise_List=self.scheduler.generate_user_dialogue()

                user_speech = self._get_user_speech_or_skip(choise_List)
                
                if user_speech == "QUIT":  # 用户选择退出
                    break
                elif user_speech is not None:  # 用户说话
                    # 输出用户回应
                    print(f"💬 {USER_CHARACTER_NAME}：{user_speech}")
                    
                    # 添加到历史记录
                    formatted_response = f"{USER_CHARACTER_NAME}：{user_speech}"
                    self.scheduler.add_to_history(formatted_response)
                    self.last_speaker = USER_CHARACTER_NAME
                    
                    self.conversation_count += 1
                    continue  # 用户说话后，下一轮直接调度AI
                # else: user_speech is None，用户跳过，继续下面的AI调度
            
            # 调度AI角色说话
            current_situation = f"这是第{round_num}轮对话"
            next_speaker = self.scheduler.decide_next_ai_speaker(current_situation)
            
            if not next_speaker:
                print("❌ 调度失败，无法确定下一个说话的角色")
                continue
            
            print(f"🎯 调度结果：{next_speaker} 说话")
            
            # AI角色说话
            character_agent = self.scheduler.get_character_agent(next_speaker)
            if not character_agent:
                print(f"❌ 未找到角色 {next_speaker} 的智能体")
                continue
            
            # 生成角色回应
            # print(current_situation)
            user_character_context = self.scheduler.get_user_character_context()
            character_response = character_agent.generate_response(current_situation, user_character_context)
            
            # 输出回应
            print(f"💬 {character_response}")
            
            # 添加到历史记录
            self.scheduler.add_to_history(character_response)
            self.last_speaker = next_speaker
            
            self.conversation_count += 1
            self.scheduler.generate_graph(round_num)
            # 在每轮之间添加分隔
            if round_num < rounds:
                print()

    def _get_user_speech_or_skip(self, choice_list) -> Optional[str]:
        """
        获取用户台词或跳过，支持语音、文本输入和选项选择

        Args:
            choice_list: 可选台词列表，为None时使用自由输入模式

        Returns:
            str: 用户的台词内容
            None: 用户选择跳过
            "QUIT": 用户选择退出
        """
        try:
            print("\n请选择输入方式：")
            print("1. 🎤 语音输入")
            print("2. ⌨️ 文本输入")
            if choice_list:
                print("3. 📋 从选项中选择")
            print("4. ⏭️ 跳过")
            print("5. 🚪 退出")

            while True:
                choice = input(f"请选择(1-{'5' if choice_list else '4'}): ").strip()

                if choice == "1":
                    # 语音输入
                    text = record_and_recognize(duration=5)
                    if text:  # 如果有识别结果
                        print(f"🔊 识别结果: {text}")
                        confirm = input("是否使用此结果？(Y/n): ").strip().lower()
                        if confirm in ['', 'y', 'yes']:
                            return text
                        else:
                            continue  # 让用户重新选择
                    else:
                        print("⚠️ 未识别到语音，请重试")
                        continue

                elif choice == "2":
                    # 文本输入
                    user_input = input("🎭 请输入您的台词: ").strip()
                    if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                        print("👋 退出对话")
                        return "QUIT"
                    elif user_input == "":
                        continue  # 空输入让用户重新选择
                    else:
                        return user_input

                elif choice == "3" and choice_list:
                    # 选项选择模式
                    print("\n可选台词：")
                    for i, option in enumerate(choice_list, 1):
                        print(f"{i}. {option}")

                    while True:
                        selection = input(f"请选择(1-{len(choice_list)}): ").strip()
                        if selection.lower() in ['quit', 'exit', '退出', 'q']:
                            print("👋 退出对话")
                            return "QUIT"
                        elif selection == "":
                            break  # 返回上级菜单

                        try:
                            index = int(selection) - 1
                            if 0 <= index < len(choice_list):
                                return choice_list[index]
                            else:
                                print(f"⚠️ 请输入1-{len(choice_list)}之间的数字")
                        except ValueError:
                            print("⚠️ 请输入有效数字")
                    continue

                elif choice == "4" if choice_list else choice == "3":
                    # 跳过
                    return None

                elif choice == "5" if choice_list else choice == "4":
                    # 退出
                    print("👋 退出对话")
                    return "QUIT"

                else:
                    print("⚠️ 无效输入，请重新选择")

        except KeyboardInterrupt:
            print("\n👋 对话被中断")
            return "QUIT"

    def interactive_conversation(self) -> None:
        """
        交互式对话模式
        """
        if not self.is_initialized:
            print("❌ 请先初始化剧本设定")
            return
        
        print("\n🎬 进入交互式对话模式")
        print("输入指令或情境描述来推进剧情")
        print("💡 优化的交互体验：")
        print("  - 当需要您说话时，直接输入台词，按回车跳过")
        print("  - 您说话后会直接调度AI角色，AI说话后才会再次询问您")
        print("📝 可用指令:")
        print("  - 'quit' 或 'exit': 退出对话模式")
        print("  - 'auto [数字]': 进行自动对话")
        print("  - 'next': 推进到下一轮对话")
        print("  - 其他文字: 作为情境描述推进剧情")
        print("=" * 60)
        
        # 重置对话状态
        if not hasattr(self, 'last_speaker'):
            self.last_speaker = None
        
        while True:
            try:
                user_input = input("\n🎮 请输入指令或情境描述: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 退出交互式对话模式")
                    break
                
                if user_input.lower().startswith('auto'):
                    # 自动对话模式
                    parts = user_input.split()
                    rounds = 5  # 默认5轮
                    if len(parts) > 1 and parts[1].isdigit():
                        rounds = int(parts[1])
                    self.start_conversation(rounds)
                    continue
                
                # 手动指定情境
                current_situation = user_input if user_input else "继续对话"
                
                # 根据上一个说话的人决定流程
                if self.last_speaker != USER_CHARACTER_NAME:
                    # 上一个不是用户说话，询问用户
                    user_speech = self._get_user_speech_or_skip()
                    
                    if user_speech == "QUIT":  # 用户选择退出
                        break
                    elif user_speech is not None:  # 用户说话
                        # 输出用户回应
                        print(f"💬 {USER_CHARACTER_NAME}：{user_speech}")
                        
                        # 添加到历史记录
                        formatted_response = f"{USER_CHARACTER_NAME}：{user_speech}"
                        self.scheduler.add_to_history(formatted_response)
                        self.last_speaker = USER_CHARACTER_NAME
                        
                        self.conversation_count += 1
                        continue  # 用户说话后，下一轮直接调度AI
                    # else: user_speech is None，用户跳过，继续下面的AI调度
                
                # 调度AI角色说话
                next_speaker = self.scheduler.decide_next_ai_speaker(current_situation)
                
                if not next_speaker:
                    print("❌ 调度失败，无法确定下一个说话的角色")
                    continue
                
                print(f"🎯 调度结果：{next_speaker} 说话")
                
                # AI角色说话
                character_agent = self.scheduler.get_character_agent(next_speaker)
                if not character_agent:
                    print(f"❌ 未找到角色 {next_speaker} 的智能体")
                    continue
                
                # 生成角色回应
                user_character_context = self.scheduler.get_user_character_context()
                character_response = character_agent.generate_response(current_situation, user_character_context)
                
                # 输出回应
                print(f"💬 {character_response}")
                
                # 添加到历史记录
                self.scheduler.add_to_history(character_response)
                self.last_speaker = next_speaker
                
                self.conversation_count += 1
                
            except KeyboardInterrupt:
                print("\n👋 退出交互式对话模式")
                break
            except Exception as e:
                print(f"❌ 发生错误: {str(e)}")
    
    def get_conversation_history(self) -> list:
        """
        获取对话历史
        
        Returns:
            对话历史列表
        """
        return self.scheduler.conversation_history.copy()
    
    def clear_history(self) -> None:
        """
        清空对话历史
        """
        self.scheduler.clear_all_history()
        self.conversation_count = 0
        self.last_speaker = None
        print("✅ 对话历史已清空")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        status = {
            "initialized": self.is_initialized,
            "conversation_count": self.conversation_count,
            "characters_count": len(self.scheduler.characters),
            "api_pool_available": self.scheduler.api_pool.get_available_count(),
            "api_pool_total": self.scheduler.api_pool.get_total_count()
        }
        
        if self.is_initialized:
            status["characters"] = self.scheduler.get_characters_info()
        
        return status
    
    def print_system_status(self) -> None:
        """
        打印系统状态
        """
        status = self.get_system_status()
        
        print("\n📊 系统状态")
        print("-" * 30)
        print(f"初始化状态: {'✅ 已初始化' if status['initialized'] else '❌ 未初始化'}")
        print(f"对话轮数: {status['conversation_count']}")
        print(f"角色数量: {status['characters_count']}")
        print(f"API池状态: {status['api_pool_available']}/{status['api_pool_total']} 可用")
        
        if status['initialized'] and status['characters_count'] > 0:
            print("\n🎭 角色列表:")
            for character in status['characters']:
                if character.get('type') == 'user':
                    print(f"  - {character['name']} (用户主角) 👤")
                else:
                    print(f"  - {character['name']} (AI角色) 🤖") 