"""
Electron Bridge - 连接前端与Python后端的API桥梁
"""

import json
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from script_system import ScriptSystem
from word_to_vi import text_to_image
import threading
import time

# 配置日志 - 设置UTF-8编码
import sys
import os

# 设置控制台输出编码
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

class ElectronBridge:
    def __init__(self, port=None):
        # 从环境变量读取端口，如果没有设置则使用默认端口8900
        if port is None:
            port = int(os.environ.get('FLASK_PORT', 8900))
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)  # 允许跨域请求
        
        # 初始化剧本系统
        try:
            self.script_system = ScriptSystem()
            logger.info("剧本系统初始化成功")
        except Exception as e:
            logger.error(f"剧本系统初始化失败: {e}")
            self.script_system = None
        
        self.setup_routes()
    
    def setup_routes(self):
        """设置API路由"""
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """获取系统状态"""
            try:
                status = {
                    'success': True,
                    'status': 'running',
                    'port': self.port,
                    'script_system_available': self.script_system is not None,
                    'timestamp': time.time()
                }
                
                if self.script_system:
                    system_status = self.script_system.get_system_status()
                    status.update(system_status)
                
                return jsonify(status)
            except Exception as e:
                logger.error(f"获取状态失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/create-script', methods=['POST'])
        def create_script():
            """创建剧本"""
            try:
                data = request.get_json()
                scene_description = data.get('sceneDescription', '').strip()
                
                if not scene_description:
                    return jsonify({
                        'success': False,
                        'error': '场景描述不能为空'
                    }), 400
                
                if not self.script_system:
                    return jsonify({
                        'success': False,
                        'error': '剧本系统未初始化'
                    }), 500
                
                logger.info(f"创建剧本请求: {scene_description}")
                
                # 调用剧本系统创建剧本
                result = self.script_system.initialize_script(scene_description)
                
                if 'error' in result:
                    return jsonify({
                        'success': False,
                        'error': result['error']
                    }), 500
                
                # 获取角色信息
                characters_info = []
                if hasattr(self.script_system.scheduler, 'get_characters_info'):
                    characters_info = self.script_system.scheduler.get_characters_info()
                
                response_data = {
                    'success': True,
                    'message': '剧本创建成功',
                    'data': {
                        'scene': scene_description,
                        'characters': [char['name'] for char in characters_info],
                        'characters_detail': characters_info,
                        'characters_count': len(characters_info)
                    }
                }
                
                logger.info(f"剧本创建成功: {len(characters_info)} 个角色")
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"创建剧本失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'创建剧本失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/send-message', methods=['POST'])
        def send_message():
            """发送用户消息并获取AI回应"""
            try:
                data = request.get_json()
                message = data.get('message', '').strip()
                round_num = data.get('round', 1)
                
                if not message:
                    message = " "
                
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                logger.info(f"收到用户消息 (第{round_num}轮): {message}")
                
                # 添加用户消息到历史记录
                user_response = f"我：{message}"
                self.script_system.scheduler.add_to_history(user_response)
                
                # 决定下一个AI角色发言
                situation = f"用户刚刚说：{message}，这是第{round_num}轮对话"
                next_speaker = self.script_system.scheduler.decide_next_ai_speaker(situation)
                
                if not next_speaker:
                    return jsonify({
                        'success': False,
                        'error': '无法确定下一个发言角色'
                    }), 500
                
                # 获取AI角色回应
                character_agent = self.script_system.scheduler.get_character_agent(next_speaker)
                if not character_agent:
                    return jsonify({
                        'success': False,
                        'error': f'找不到角色 {next_speaker} 的智能体'
                    }), 500
                
                # 获取用户角色信息
                user_character_context = self.script_system.scheduler.get_user_character_context()
                
                # 生成AI回应
                ai_response = character_agent.generate_response(situation, user_character_context)
                
                # 添加AI回应到历史记录
                self.script_system.scheduler.add_to_history(ai_response)
                
                # 检查并触发后台图片生成（每3轮对话）
                self.script_system.check_and_trigger_background_image_generation(round_num)
                
                response_data = {
                    'success': True,
                    'response': ai_response,
                    'speaker': next_speaker,
                    'round': round_num,
                    'situation': situation
                }
                
                logger.info(f"AI回应 ({next_speaker}): {ai_response[:100]}...")
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"处理消息失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'处理消息失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/start-conversation', methods=['POST'])
        def start_conversation():
            """开始自动对话"""
            try:
                data = request.get_json()
                rounds = data.get('rounds', 5)
                
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                logger.info(f"开始自动对话: {rounds} 轮")
                
                # 在后台线程中执行对话
                def run_conversation():
                    try:
                        self.script_system.start_conversation(rounds)
                    except Exception as e:
                        logger.error(f"自动对话执行失败: {e}")
                
                conversation_thread = threading.Thread(target=run_conversation)
                conversation_thread.daemon = True
                conversation_thread.start()
                
                return jsonify({
                    'success': True,
                    'message': f'开始 {rounds} 轮自动对话',
                    'rounds': rounds
                })
                
            except Exception as e:
                logger.error(f"启动对话失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'启动对话失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/clear-history', methods=['POST'])
        def clear_history():
            """清空对话历史"""
            try:
                if self.script_system:
                    self.script_system.clear_history()
                
                logger.info("对话历史已清空")
                return jsonify({
                    'success': True,
                    'message': '对话历史已清空'
                })
                
            except Exception as e:
                logger.error(f"清空历史失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'清空历史失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/voice-start', methods=['POST'])
        def voice_start():
            """开始语音录音"""
            try:
                from web_voice_recorder import voice_recorder
                
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                logger.info("开始语音录音")
                result = voice_recorder.start_recording()
                
                if result['success']:
                    logger.info("语音录音已开始")
                else:
                    logger.error(f"开始录音失败: {result['error']}")
                
                return jsonify(result)
                
            except ImportError as e:
                logger.error(f"语音录音模块导入失败: {e}")
                return jsonify({
                    'success': False,
                    'error': '语音录音功能不可用'
                }), 500
            except Exception as e:
                logger.error(f"开始录音失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'开始录音失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/voice-stop', methods=['POST'])
        def voice_stop():
            """停止语音录音并识别"""
            try:
                from web_voice_recorder import voice_recorder
                
                data = request.get_json()
                round_num = data.get('round', 1)
                
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                logger.info(f"停止语音录音并识别 (第{round_num}轮)")
                
                # 停止录音并识别
                result = voice_recorder.stop_recording_and_recognize()
                
                if result['success']:
                    recognized_text = result['recognized_text']
                    logger.info(f"语音识别结果: {recognized_text}")
                    
                    # 直接将识别结果作为用户发言处理
                    user_response = f"我：{recognized_text}"
                    self.script_system.scheduler.add_to_history(user_response)
                    self.script_system.last_speaker = "我"
                    self.script_system.conversation_count += 1
                    
                    return jsonify({
                        'success': True,
                        'recognized_text': recognized_text,
                        'formatted_message': user_response,
                        'round': round_num
                    })
                else:
                    logger.error(f"语音识别失败: {result['error']}")
                    return jsonify(result), 400
                
            except ImportError as e:
                logger.error(f"语音录音模块导入失败: {e}")
                return jsonify({
                    'success': False,
                    'error': '语音录音功能不可用'
                }), 500
            except Exception as e:
                logger.error(f"停止录音失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'停止录音失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/voice-status', methods=['GET'])
        def voice_status():
            """获取语音录音状态"""
            try:
                from web_voice_recorder import voice_recorder
                result = voice_recorder.get_status()
                return jsonify({
                    'success': True,
                    'is_recording': result['is_recording']
                })
            except ImportError as e:
                return jsonify({
                    'success': False,
                    'error': '语音录音功能不可用'
                }), 500
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'获取状态失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/get-dialogue-options', methods=['POST'])
        def get_dialogue_options():
            """获取用户对话选项"""
            try:
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                data = request.get_json()
                round_num = data.get('round', 1)
                
                logger.info(f"获取用户对话选项 (第{round_num}轮)")
                
                # 生成对话选项
                dialogue_options = self.script_system.scheduler.generate_user_dialogue()
                
                if dialogue_options and len(dialogue_options) > 0:
                    logger.info(f"生成对话选项: {dialogue_options}")
                    return jsonify({
                        'success': True,
                        'options': dialogue_options,
                        'round': round_num
                    })
                else:
                    logger.warning("未能生成有效的对话选项")
                    return jsonify({
                        'success': False,
                        'error': '无法生成对话选项'
                    }), 500
                
            except Exception as e:
                logger.error(f"获取对话选项失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'获取对话选项失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/select-dialogue', methods=['POST'])
        def select_dialogue():
            """选择对话选项"""
            try:
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                data = request.get_json()
                selected_text = data.get('selected_text', '').strip()
                round_num = data.get('round', 1)
                
                if not selected_text:
                    return jsonify({
                        'success': False,
                        'error': '选择的对话内容不能为空'
                    }), 400
                
                logger.info(f"用户选择对话 (第{round_num}轮): {selected_text}")
                
                # 从选择的台词中提取角色信息
                import re
                character_match = re.match(r'^\[([^\]]+)\]\s*(.+)', selected_text)
                
                if character_match:
                    character_name = character_match.group(1)
                    dialogue_content = character_match.group(2)
                    
                    # 如果是历史人物角色，设置用户当前扮演的角色
                    if character_name != "用户" and character_name != "我":
                        success = self.script_system.scheduler.set_user_character(character_name)
                        if success:
                            logger.info(f"✅ 用户角色已设置为: {character_name}")
                        else:
                            logger.warning(f"⚠️ 设置用户角色失败: {character_name}")
                    
                    # 将选择的对话作为用户发言处理，使用实际台词内容
                    user_response = f"我：{dialogue_content}"
                    formatted_message = user_response
                    display_character = character_name
                else:
                    # 如果没有角色标记，直接使用原文本
                    dialogue_content = selected_text
                    user_response = f"我：{selected_text}"
                    formatted_message = user_response
                    display_character = "我"
                
                self.script_system.scheduler.add_to_history(user_response)
                self.script_system.last_speaker = "我"
                self.script_system.conversation_count += 1
                
                response_data = {
                    'success': True,
                    'selected_text': selected_text,
                    'dialogue_content': dialogue_content,
                    'character_name': display_character,
                    'formatted_message': formatted_message,
                    'round': round_num
                }
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"选择对话失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'选择对话失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/next-speaker', methods=['POST'])
        def get_next_speaker():
            """获取下一个说话的角色"""
            try:
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                data = request.get_json()
                round_num = data.get('round', 1)
                situation = data.get('situation', f'这是第{round_num}轮对话')
                
                logger.info(f"获取下一个说话角色 (第{round_num}轮)")
                
                # 根据最后一个说话的人决定流程
                last_speaker = getattr(self.script_system, 'last_speaker', None)
                
                if last_speaker != "我":
                    # 上一个不是用户说话（或者是第一轮），应该询问用户
                    return jsonify({
                        'success': True,
                        'next_speaker': '我',
                        'speaker_type': 'user',
                        'action': 'ask_user',
                        'message': '现在轮到您说话了',
                        'round': round_num
                    })
                else:
                    # 用户刚说完，调度AI角色
                    next_speaker = self.script_system.scheduler.decide_next_ai_speaker(situation)
                    
                    if not next_speaker:
                        return jsonify({
                            'success': False,
                            'error': '无法确定下一个发言角色'
                        }), 500
                    
                    return jsonify({
                        'success': True,
                        'next_speaker': next_speaker,
                        'speaker_type': 'ai',
                        'action': 'ai_speak',
                        'message': f'下一个说话的是：{next_speaker}',
                        'round': round_num
                    })
                
            except Exception as e:
                logger.error(f"获取下一个说话角色失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'获取下一个说话角色失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/user-speak', methods=['POST'])
        def user_speak():
            """用户说话"""
            try:
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                data = request.get_json()
                original_message = data.get('message', '')
                message = original_message.strip()
                round_num = data.get('round', 1)
                action = data.get('action', 'speak')  # 'speak' 或 'skip'
                
                if action == 'skip':
                    # 用户选择跳过
                    logger.info(f"用户跳过发言 (第{round_num}轮)")
                    return jsonify({
                        'success': True,
                        'action': 'skip',
                        'message': '用户选择跳过',
                        'round': round_num
                    })
                
                # 如果原始消息是换行符，视为跳过
                if original_message == '\n':
                    logger.info(f"用户发送换行符跳过发言 (第{round_num}轮)")
                    # 添加换行符到历史记录，表示用户跳过
                    user_response = f"我：\\n"
                    self.script_system.scheduler.add_to_history(user_response)
                    self.script_system.last_speaker = "我"
                    self.script_system.conversation_count += 1
                    
                    return jsonify({
                        'success': True,
                        'action': 'speak',
                        'message': '\n',
                        'formatted_message': user_response,
                        'round': round_num
                    })
                
                if not message:
                    return jsonify({
                        'success': False,
                        'error': '消息内容不能为空'
                    }), 400
                
                logger.info(f"用户发言 (第{round_num}轮): {message}")
                
                # 添加用户消息到历史记录
                user_response = f"我：{message}"
                self.script_system.scheduler.add_to_history(user_response)
                self.script_system.last_speaker = "我"
                self.script_system.conversation_count += 1
                
                return jsonify({
                    'success': True,
                    'action': 'speak',
                    'message': message,
                    'formatted_message': user_response,
                    'round': round_num
                })
                
            except Exception as e:
                logger.error(f"用户发言失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'用户发言失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/ai-speak', methods=['POST'])
        def ai_speak():
            """AI角色说话"""
            try:
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                data = request.get_json()
                speaker = data.get('speaker', '').strip()
                round_num = data.get('round', 1)
                situation = data.get('situation', f'这是第{round_num}轮对话')
                
                if not speaker:
                    return jsonify({
                        'success': False,
                        'error': '说话角色不能为空'
                    }), 400
                
                logger.info(f"AI角色发言 (第{round_num}轮): {speaker}")
                
                # 获取AI角色智能体
                character_agent = self.script_system.scheduler.get_character_agent(speaker)
                if not character_agent:
                    return jsonify({
                        'success': False,
                        'error': f'找不到角色 {speaker} 的智能体'
                    }), 500
                
                # 获取用户角色信息
                user_character_context = self.script_system.scheduler.get_user_character_context()
                
                # 生成AI回应
                ai_response = character_agent.generate_response(situation, user_character_context)
                
                # 添加AI回应到历史记录
                self.script_system.scheduler.add_to_history(ai_response)
                self.script_system.last_speaker = speaker
                self.script_system.conversation_count += 1
                
                # 检查并触发后台图片生成（每3轮对话）
                self.script_system.check_and_trigger_background_image_generation(round_num)
                
                return jsonify({
                    'success': True,
                    'speaker': speaker,
                    'message': ai_response,
                    'round': round_num
                })
                
            except Exception as e:
                logger.error(f"AI角色发言失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'AI角色发言失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/get-history', methods=['GET'])
        def get_history():
            """获取对话历史"""
            try:
                if not self.script_system:
                    return jsonify({
                        'success': False,
                        'error': '剧本系统未初始化'
                    }), 500
                
                history = self.script_system.get_conversation_history()
                
                return jsonify({
                    'success': True,
                    'history': history,
                    'count': len(history)
                })
                
            except Exception as e:
                logger.error(f"获取历史失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'获取历史失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/system-info', methods=['GET'])
        def get_system_info():
            """获取系统详细信息"""
            try:
                info = {
                    'success': True,
                    'bridge_status': 'running',
                    'port': self.port,
                    'script_system_available': self.script_system is not None
                }
                
                if self.script_system:
                    system_status = self.script_system.get_system_status()
                    info.update(system_status)
                    
                    # 获取角色信息
                    if hasattr(self.script_system.scheduler, 'get_characters_info'):
                        characters_info = self.script_system.scheduler.get_characters_info()
                        info['characters'] = characters_info
                
                return jsonify(info)
                
            except Exception as e:
                logger.error(f"获取系统信息失败: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/get-user-character', methods=['GET'])
        def get_user_character():
            """获取用户当前扮演的角色信息"""
            try:
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                character_name, character_info = self.script_system.scheduler.get_user_character()
                
                return jsonify({
                    'success': True,
                    'user_character': character_name,
                    'character_info': character_info,
                    'has_character': character_name is not None
                })
                
            except Exception as e:
                logger.error(f"获取用户角色失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'获取用户角色失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/reset-user-character', methods=['POST'])
        def reset_user_character():
            """重置用户角色，允许重新选择"""
            try:
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                self.script_system.scheduler.clear_user_character()
                logger.info("用户角色已重置")
                
                return jsonify({
                    'success': True,
                    'message': '角色已重置，可以重新选择'
                })
                
            except Exception as e:
                logger.error(f"重置用户角色失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'重置用户角色失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/generate-scene-image', methods=['POST'])
        def generate_scene_image():
            """根据场景设定生成图片"""
            try:
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                # 获取场景设定
                scene_setting = getattr(self.script_system.scheduler, 'scene_setting', '')
                
                if not scene_setting:
                    return jsonify({
                        'success': False,
                        'error': '场景设定为空，无法生成图片'
                    }), 400
                
                logger.info(f"开始生成场景图片，场景设定: {scene_setting[:100]}...")
                
                # 构建图片生成的prompt
                prompt = f"古代中国历史场景，{scene_setting}，电影级别画质，史诗级场面，高清细节"
                
                # 创建保存目录
                save_dir = os.path.join(os.path.dirname(__file__), 'scene_images')
                
                # 生成图片
                image_path = text_to_image(prompt, save_dir)
                
                if image_path and os.path.exists(image_path):
                    # 保存图片路径到剧本系统
                    self.script_system.current_scene_image = image_path
                    
                    logger.info(f"场景图片生成成功: {image_path}")
                    return jsonify({
                        'success': True,
                        'image_path': image_path,
                        'message': '场景图片生成成功'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '图片生成失败'
                    }), 500
                
            except Exception as e:
                logger.error(f"生成场景图片失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'生成场景图片失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/get-scene-image', methods=['GET'])
        def get_scene_image():
            """获取当前场景图片"""
            try:
                if not self.script_system:
                    return jsonify({
                        'success': False,
                        'error': '剧本系统未初始化'
                    }), 400
                
                # 检查是否有当前场景图片
                image_path = getattr(self.script_system, 'current_scene_image', None)
                
                if image_path and os.path.exists(image_path):
                    return send_file(image_path, mimetype='image/png')
                else:
                    return jsonify({
                        'success': False,
                        'error': '暂无场景图片'
                    }), 404
                
            except Exception as e:
                logger.error(f"获取场景图片失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'获取场景图片失败: {str(e)}'
                }), 500
        
        @self.app.route('/api/get-scene-image-url', methods=['GET'])
        def get_scene_image_url():
            """获取当前场景图片URL"""
            try:
                if not self.script_system or not self.script_system.is_initialized:
                    return jsonify({
                        'success': False,
                        'error': '请先创建剧本设定'
                    }), 400
                
                # 获取当前图片路径
                image_path = self.script_system.scheduler.get_current_image_path()
                
                if image_path and os.path.exists(image_path):
                    # 将绝对路径转换为相对于backg目录的路径
                    relative_path = os.path.relpath(image_path, os.getcwd())
                    image_url = f"/image/{relative_path.replace(os.sep, '/')}"
                    
                    return jsonify({
                        'success': True,
                        'image_url': image_url,
                        'image_path': image_path
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '暂无可用的场景图片'
                    })
                    
            except Exception as e:
                logger.error(f"获取场景图片失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'获取场景图片失败: {str(e)}'
                }), 500
        
        @self.app.route('/image/<path:filename>')
        def serve_image(filename):
            """提供图片文件服务"""
            try:
                # 构建完整的文件路径
                file_path = os.path.join(os.getcwd(), filename)
                
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    logger.error(f"图片文件不存在: {file_path}")
                    return jsonify({'error': '图片文件不存在'}), 404
                
                # 检查文件扩展名
                allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in allowed_extensions:
                    return jsonify({'error': '不支持的文件格式'}), 400
                
                logger.info(f"提供图片文件: {file_path}")
                return send_file(file_path)
                
            except Exception as e:
                logger.error(f"提供图片文件失败: {e}")
                return jsonify({'error': f'提供图片文件失败: {str(e)}'}), 500

        @self.app.route('/', methods=['GET'])
        def root():
            """根路径 - 返回API信息"""
            return jsonify({
                'success': True,
                'service': '浮生：多Agent驱动的沉浸式文化互动剧场 - Electron Bridge',
                'version': '1.0.0',
                'status': 'running',
                'port': self.port,
                'endpoints': {
                    'status': '/api/status',
                    'system_info': '/api/system-info',
                    'create_script': '/api/create-script',
                    'send_message': '/api/send-message',
                    'start_conversation': '/api/start-conversation',
                    'clear_history': '/api/clear-history',
                    'get_history': '/api/get-history'
                }
            })
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'API endpoint not found',
                'message': '请使用正确的API端点，访问根路径 / 查看可用端点列表'
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    def run(self, debug=False):
        """启动Flask服务器"""
        try:
            logger.info(f"启动Electron Bridge服务器，端口: {self.port}")
            self.app.run(
                host='127.0.0.1',
                port=self.port,
                debug=debug,
                threaded=True,
                use_reloader=False  # 避免重复启动
            )
        except Exception as e:
            logger.error(f"启动服务器失败: {e}")
            raise

def main():
    """主函数"""
    bridge = ElectronBridge()  # 使用默认端口配置
    
    try:
        bridge.run(debug=False)
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")

if __name__ == "__main__":
    main() 